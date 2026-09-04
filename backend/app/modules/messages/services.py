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
from app.modules.memory.services import UnifiedMemoryManager
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
        memory_manager: UnifiedMemoryManager,
    ):
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository
        self.llm = llm
        self.conversation_service = conversation_service
        self.memory_manager = memory_manager

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

    def get_messages_by_conversation(self, conversation_id: str):
        """Get all messages for a specific conversation."""
        return self.message_repository.get_messages_by_conversation(conversation_id)

    async def send_message(self, conversation_data: ConversationCreate):
        """Send a message in a conversation and stream the response from the LLM with 4-layer memory."""

        # -----------------------------------
        # 1. GET OR CREATE CONVERSATION
        # -----------------------------------
        initial_title = (
            conversation_data.message[:50]
            if isinstance(conversation_data.message, str)
            else "New Chat"
        )

        # In production, pass authenticated user_id from token/context
        user_id = uuid.UUID("12345678-1234-4234-8234-123456789abc")

        _conversation = Conversation(
            title=initial_title,
            user_id=user_id,
        )

        if conversation_data.conversation_id:
            _conversation.conversation_id = conversation_data.conversation_id

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
        current_user_text = self._extract_text_content(user_content)
        parent_id = conversation.last_message_id

        user_message = Message(
            conversation_id=conversation.conversation_id,
            content=user_content,
            parent_message_id=parent_id,
            role="user",
        )

        self.message_repository.create(user_message)
        self.message_repository.session.commit()
        self.message_repository.session.refresh(user_message)

        # Update conversation tail pointer
        conversation.last_message_id = user_message.message_id
        conversation.updated_at = datetime.now(timezone.utc)
        self.conversation_repository.session.commit()

        # -----------------------------------
        # 3. CREATE ASSISTANT PLACEHOLDER
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
        # 5. RETRIEVE ALL 4 MEMORY LAYERS
        # -----------------------------------
        conv_id = conversation.conversation_id

        # Layer 4: Entity / User Profile Memory (Cross-session facts)
        profile_facts = await self.memory_manager.get_user_profile_facts(user_id)
        profile_text = (
            "\n".join(profile_facts)
            if profile_facts
            else "No saved user profile facts."
        )

        # Layer 2: Summary Memory (Condensation of older turns)
        summary = await self.memory_manager.get_summary(conv_id)
        summary_text = summary if summary else "No previous summary."

        # Layer 3: Semantic / Vector Memory (Episodic retrieval based on current query)
        relevant_chunks = await self.memory_manager.retrieve_relevant_context(
            conversation_id=conv_id, query=current_user_text, top_k=2
        )
        semantic_text = (
            "\n".join(relevant_chunks)
            if relevant_chunks
            else "No additional relevant past context."
        )

        # Layer 1: Buffer Memory (Sliding window of last 6 raw turns)
        last_messages = await self.memory_manager.get_buffer_memory(conv_id, limit=6)

        # -----------------------------------
        # 6. ASSEMBLE SYSTEM PROMPT & HISTORY
        # -----------------------------------
        system_memory_prompt = f"""
            You are a helpful AI assistant. Use the long-term context, facts, and conversation history below to maintain continuity.

            [USER PROFILE & PREFERENCES]
            {profile_text}

            [CONVERSATION BACKGROUND SUMMARY]
            {summary_text}

            [RELEVANT RETRIEVED PAST CONTEXT]
            {semantic_text}
            """

        history_prompts: list[str] = [system_memory_prompt]

        # Append recent buffer turns chronologically
        if last_messages:
            sorted_history = sorted(last_messages, key=lambda m: m.created_at)
            for msg in sorted_history:
                # Exclude the current user message and placeholder assistant message
                if msg.message_id in (
                    user_message.message_id,
                    assistant_message.message_id,
                ):
                    continue
                text = self._extract_text_content(msg.content)
                if text:
                    history_prompts.append(f"{msg.role.capitalize()}: {text}")

        # Append the active user query as the final prompt entry
        history_prompts.append(f"User: {current_user_text}")

        # -----------------------------------
        # 7. STREAM LLM RESPONSE
        # -----------------------------------
        full_response = ""
        full_thinking = ""
        try:
            async for chunk in self.llm.stream(history_prompts):
                message_type = ChatEventType.TOKEN.value
                if chunk["type"] == "text":
                    full_response += chunk["content"]
                elif chunk["type"] == "thinking":
                    message_type = ChatEventType.THINKING.value
                    full_thinking += chunk["content"]

                yield self._format_sse(
                    event=message_type,
                    data={
                        "assistant_message_id": str(assistant_message.message_id),
                        "content": chunk,
                    },
                )

            # -----------------------------------
            # 8. FINALIZE ASSISTANT MESSAGE
            # -----------------------------------
            assistant_message.content = [{"type": "text", "text": full_response}]
            assistant_message.status = {"type": "complete", "reason": "stop"}

            self.message_repository.update(assistant_message)

            # Update conversation tail pointer
            conversation.last_message_id = assistant_message.message_id
            conversation.updated_at = datetime.now(timezone.utc)
            self.conversation_repository.session.commit()

            # -----------------------------------
            # 9. TRIGGER ASYNC BACKGROUND MEMORY TASKS
            # -----------------------------------
            # Run memory compression & profile extraction in the background
            asyncio.create_task(
                self.memory_manager.update_summary_if_needed(conversation_id=conv_id)
            )
            asyncio.create_task(
                self.memory_manager.extract_and_store_user_facts(
                    user_id=user_id, user_text=current_user_text
                )
            )

            # -----------------------------------
            # 10. SEND COMPLETE EVENT
            # -----------------------------------
            yield self._format_sse(
                event=ChatEventType.COMPLETE.value,
                data={
                    "conversation_id": str(conversation.conversation_id),
                    "assistant_message_id": str(assistant_message.message_id),
                },
            )

        except asyncio.CancelledError:
            # Save partial response when connection drops
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
            raise
