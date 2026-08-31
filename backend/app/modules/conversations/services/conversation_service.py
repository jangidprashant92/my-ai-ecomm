import asyncio
import json

from app.models.conversation import Conversation, Message
from app.modules.conversations.repository import (
    ConversationsRepository,
    MessagesRepository,
)
from app.modules.conversations.schemas import ConversationCreate
from app.modules.conversations.services.llm_service import LLMService


class ConversationsService:
    def __init__(
        self,
        repository: ConversationsRepository,
        message_repository: MessagesRepository,
    ):
        self.repository = repository
        self.message_repository = message_repository
        self.llm_service = LLMService()

    def _format_sse(self, event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    async def send_message(self, conversation_data: ConversationCreate):
        # -----------------------------------
        # 1. GET OR CREATE CONVERSATION
        # -----------------------------------

        conversation = self._get_or_create_conversation(conversation_data)

        # -----------------------------------
        # 2. CREATE USER MESSAGE
        # -----------------------------------

        user_message = Message(
            conversation_id=conversation.conversation_id,
            content=conversation_data.message,
            parent_message_id=None,
            role="user",
        )

        self.message_repository.create(user_message)

        self.repository.session.commit()

        self.repository.session.refresh(user_message)

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

        self.repository.session.commit()

        self.repository.session.refresh(assistant_message)

        # -----------------------------------
        # 4. SEND IDS TO FRONTEND
        # -----------------------------------

        yield self._format_sse(
            event="message_start",
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
            async for chunk in self.llm_service.stream_chat(user_message.content):
                full_response += chunk

                yield self._format_sse(
                    event="token",
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

            self.repository.session.commit()

            # -----------------------------------
            # 7. SEND COMPLETE EVENT
            # -----------------------------------

            yield self._format_sse(
                event="complete",
                data={
                    "conversation_id": str(conversation.conversation_id),
                    "assistant_message_id": str(assistant_message.message_id),
                },
            )

        except asyncio.CancelledError:
            # Save partial response

            assistant_message.content = full_response

            self.message_repository.update(assistant_message)

            self.repository.session.commit()

            raise

    def _get_or_create_conversation(
        self, conversation_data: ConversationCreate
    ) -> Conversation:
        # Check if a conversation with the same title exists
        if conversation_data.conversation_id:
            exiting = self.repository.get_by_id(
                conversation_id=conversation_data.conversation_id
            )
            if exiting:
                return exiting

        return self.repository.create(conversation_data)
