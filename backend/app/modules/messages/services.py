import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.ai.llm.base import BaseLLMProvider
from app.models.conversation import Conversation, Message
from app.modules.conversations.repository import ConversationsRepository
from app.modules.conversations.schemas import ConversationCreate
from app.modules.conversations.services import ConversationsService
from app.modules.messages.repository import MessagesRepository
from app.modules.messages.schemas import ChatEventType


class MessagesService:
    """Service for managing messages."""

    def __init__(
        self,
        conversation_repository: ConversationsRepository,
        message_repository: MessagesRepository,
        llm: BaseLLMProvider,
        conversation_service: ConversationsService,
    ):
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository
        self.llm = llm
        self.conversation_service = conversation_service

    def _format_sse(self, event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    def _extract_text_content(self, content: list[dict[str, Any]]) -> str:
        """Extract plain text string from multi-modal content list for the LLM."""
        text_parts = [
            part["text"]
            for part in content
            if isinstance(part, dict) and part.get("type") == "text" and "text" in part
        ]
        return "\n".join(text_parts)

    def _format_user_content(self, message_input: Any) -> list[dict[str, Any]]:
        """Normalize string or list input into a valid ThreadMessageLike content list."""
        if isinstance(message_input, list):
            return message_input
        return [{"type": "text", "text": str(message_input)}]

    async def send_message(self, conversation_data: ConversationCreate):
        """Send a message in a conversation and stream the response from the LLM."""

        # -----------------------------------
        # 1. GET OR CREATE CONVERSATION
        # -----------------------------------
        initial_title = (
            conversation_data.message[:50]
            if isinstance(conversation_data.message, str)
            else "New Chat"
        )

        _conversation = Conversation(
            title=initial_title,
            user_id=uuid.UUID("12345678-1234-4234-8234-123456789abc"),
        )

        last_messages: list[Message] = []
        if conversation_data.conversation_id:
            _conversation.conversation_id = conversation_data.conversation_id
            # Retrieve past context
            last_messages = await self.message_repository.get_last_messages(
                conversation_id=conversation_data.conversation_id, limit=5
            )

        conversation = await self.conversation_service.get_or_create_conversation(
            _conversation
        )
        self.conversation_repository.session.commit()
        self.conversation_repository.session.refresh(conversation)

        if not conversation.conversation_id:
            raise ValueError("Conversation ID is missing after creation.")

        # -----------------------------------
        # 2. CREATE USER MESSAGE (STRUCTURED JSON)
        # -----------------------------------
        user_content = self._format_user_content(conversation_data.message)

        # Parent is either the conversation's current last message or None
        parent_id = conversation.last_message_id

        user_message = Message(
            conversation_id=conversation.conversation_id,
            content=user_content,
            parent_message_id=parent_id,
            role="user",
            status={"type": "complete"},
        )

        self.message_repository.create(user_message)
        self.message_repository.session.commit()
        self.message_repository.session.refresh(user_message)

        # Update conversation tail pointer to user message
        conversation.last_message_id = user_message.message_id
        conversation.updated_at = datetime.now(timezone.utc)
        self.conversation_repository.session.commit()

        # -----------------------------------
        # 3. CREATE ASSISTANT PLACEHOLDER (STRUCTURED JSON)
        # -----------------------------------
        assistant_message = Message(
            conversation_id=conversation.conversation_id,
            content=[{"type": "text", "text": ""}],
            parent_message_id=user_message.message_id,
            role="assistant",
            status={"type": "running"},
        )

        self.message_repository.create(assistant_message)
        self.message_repository.session.commit()
        self.message_repository.session.refresh(assistant_message)

        # -----------------------------------
        # 4. SEND INITIAL IDS TO FRONTEND
        # -----------------------------------
        yield self._format_sse(
            event=ChatEventType.MESSAGE_START.value,
            data={
                "conversation_id": str(conversation.conversation_id),
                "user_message_id": str(user_message.message_id),
                "assistant_message_id": str(assistant_message.message_id),
            },
        )

        # -----------------------------------
        # 5. PREPARE LLM INPUT & STREAM RESPONSE
        # -----------------------------------
        # Build prompt list with previous history + current query
        history_prompts: list[str] = []
        if last_messages:
            # Sort chronologically if repository returns them descending
            sorted_history = sorted(last_messages, key=lambda m: m.created_at)
            for msg in sorted_history:
                text = self._extract_text_content(msg.content)
                if text:
                    history_prompts.append(f"{msg.role.capitalize()}: {text}")

        current_user_text = self._extract_text_content(user_content)
        history_prompts.append(f"User: {current_user_text}")

        full_response = ""

        try:
            async for chunk in self.llm.stream(history_prompts):
                full_response += chunk

                yield self._format_sse(
                    event=ChatEventType.TOKEN.value,
                    data={
                        "assistant_message_id": str(assistant_message.message_id),
                        "content": chunk,
                    },
                )

            # -----------------------------------
            # 6. FINALIZE ASSISTANT MESSAGE
            # -----------------------------------
            assistant_message.content = [{"type": "text", "text": full_response}]
            assistant_message.status = {"type": "complete", "reason": "stop"}

            self.message_repository.update(assistant_message)

            # Update conversation tail pointer to assistant message
            conversation.last_message_id = assistant_message.message_id
            conversation.updated_at = datetime.now(timezone.utc)
            self.conversation_repository.session.commit()

            # -----------------------------------
            # 7. SEND COMPLETE EVENT
            # -----------------------------------
            yield self._format_sse(
                event=ChatEventType.COMPLETE.value,
                data={
                    "conversation_id": str(conversation.conversation_id),
                    "assistant_message_id": str(assistant_message.message_id),
                },
            )

        except asyncio.CancelledError:
            # Save partial text on connection drop
            assistant_message.content = [{"type": "text", "text": full_response}]
            assistant_message.status = {"type": "incomplete", "reason": "cancelled"}
            self.message_repository.update(assistant_message)
            self.message_repository.session.commit()
            raise

        except Exception as e:
            assistant_message.content = [{"type": "text", "text": full_response}]
            assistant_message.status = {"type": "incomplete", "reason": "error"}
            self.message_repository.update(assistant_message)
            self.message_repository.session.commit()

            yield self._format_sse(
                event=ChatEventType.ERROR.value,
                data={"error": str(e)},
            )
            raise e

    def get_messages_by_conversation(self, conversation_id: str):
        """Get all messages for a specific conversation."""
        return self.message_repository.get_messages_by_conversation(conversation_id)
