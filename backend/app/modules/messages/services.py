import asyncio
import json
import uuid

from app.ai.llm.base import BaseLLMProvider
from app.models.conversation import Conversation, Message
from app.modules.conversations.repository import (
    ConversationsRepository,
)
from app.modules.conversations.schemas import (
    ConversationCreate,
)
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
        conversation_service: ConversationsService,  # Forward reference to avoid circular import
    ):
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository
        self.llm = llm
        self.conversation_service = conversation_service

    def _format_sse(self, event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    async def send_message(self, conversation_data: ConversationCreate):
        """Send a message in a conversation and stream the response from the LLM."""
        # -----------------------------------
        # 1. GET OR CREATE CONVERSATION
        # -----------------------------------

        conversation = await self.conversation_service.get_or_create_conversation(
            Conversation(
                title=conversation_data.message,
                user_id=uuid.UUID("12345678-1234-4234-8234-123456789abc"),
            )
        )

        self.conversation_repository.session.commit()

        self.conversation_repository.session.refresh(conversation)

        # -----------------------------------
        # 2. CREATE USER MESSAGE
        # -----------------------------------

        if not conversation.conversation_id:
            raise ValueError("Conversation ID is missing after creation.")

        user_message = Message(
            conversation_id=conversation.conversation_id,
            content=conversation_data.message,
            parent_message_id=None,
            role="user",
        )

        self.message_repository.create(user_message)

        self.message_repository.session.commit()

        self.message_repository.session.refresh(user_message)

        # -----------------------------------
        # 3. CREATE ASSISTANT MESSAGE FIRST
        # -----------------------------------

        assistant_message = Message(
            conversation_id=conversation.conversation_id,
            content="",
            parent_message_id=user_message.message_id,
            role="assistant",
            # status="generating"
        )

        self.message_repository.create(assistant_message)

        self.message_repository.session.commit()

        self.message_repository.session.refresh(assistant_message)

        # -----------------------------------
        # 4. SEND IDS TO FRONTEND
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
        # 5. STREAM LLM RESPONSE
        # -----------------------------------

        full_response = ""

        try:
            async for chunk in self.llm.stream([user_message.content]):
                full_response += chunk

                yield self._format_sse(
                    event=ChatEventType.TOKEN.value,
                    data={
                        "assistant_message_id": str(assistant_message.message_id),
                        "content": chunk,
                    },
                )

            # -----------------------------------
            # 6. UPDATE ASSISTANT MESSAGE
            # -----------------------------------

            assistant_message.content = full_response

            self.message_repository.update(assistant_message)

            self.message_repository.session.commit()

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
            # Save partial response

            assistant_message.content = full_response

            self.message_repository.update(assistant_message)

            self.message_repository.session.commit()

            raise
