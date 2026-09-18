import asyncio
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from app.ai.graph.state import GraphContext
from app.models.conversation import Message
from app.modules.conversations.repository import ConversationsRepository
from app.modules.conversations.schemas import ConversationCreate
from app.modules.conversations.services import ConversationsService
from app.modules.messages.repository import MessagesRepository
from app.modules.messages.schemas import ChatEventType


class MessagesService:
    """Application service for chat message persistence and graph execution."""

    def __init__(
        self,
        conversation_repository: ConversationsRepository,
        message_repository: MessagesRepository,
        conversation_service: ConversationsService,
        chat_graph: Any,
    ):
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository
        self.conversation_service = conversation_service
        self.chat_graph = chat_graph

    def _format_sse(
        self,
        event: str,
        data: dict[str, Any],
    ) -> str:
        return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"

    def _format_user_content(
        self,
        message_input: Any,
    ) -> list[dict[str, Any]]:
        if isinstance(message_input, list):
            return message_input

        return [
            {
                "type": "text",
                "text": str(message_input),
            }
        ]

    def _extract_text_content(
        self,
        content: Any,
    ) -> str:
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts: list[str] = []

            for item in content:
                if isinstance(item, str):
                    parts.append(item)

                elif isinstance(item, dict):
                    text = item.get("text")

                    if text:
                        parts.append(str(text))

            return "".join(parts)

        return ""

    def get_messages_by_conversation(
        self,
        conversation_id: uuid.UUID,
    ):
        return self.message_repository.get_messages_by_conversation(
            conversation_id,
        )

    async def send_message(
        self,
        conversation_data: ConversationCreate,
    ):
        user_id = uuid.UUID("12345678-1234-4234-8234-123456789abc")

        current_user_text = str(conversation_data.message)

        # --------------------------------------------------
        # 1. GET OR CREATE CONVERSATION
        # --------------------------------------------------

        conversation = await self.conversation_service.get_or_create_conversation(
            conversation_id=conversation_data.conversation_id,
            title=current_user_text[:50],
            user_id=user_id,
        )

        self.conversation_repository.session.commit()
        self.conversation_repository.session.refresh(conversation)

        conversation_id = conversation.conversation_id

        if not conversation_id:
            raise ValueError("Conversation ID is missing.")

        # --------------------------------------------------
        # 2. CREATE USER MESSAGE
        # --------------------------------------------------

        user_content = self._format_user_content(conversation_data.message)

        user_message = Message(
            conversation_id=conversation_id,
            content=user_content,
            parent_message_id=conversation.last_message_id,
            role="user",
        )

        self.message_repository.create(user_message)
        self.message_repository.session.commit()
        self.message_repository.session.refresh(user_message)

        # --------------------------------------------------
        # 3. CREATE ASSISTANT PLACEHOLDER
        # --------------------------------------------------

        assistant_message = Message(
            conversation_id=conversation_id,
            content=[
                {
                    "type": "text",
                    "text": "",
                }
            ],
            parent_message_id=user_message.message_id,
            role="assistant",
            status={"type": "running"},
        )

        self.message_repository.create(assistant_message)

        self.message_repository.session.commit()
        self.message_repository.session.refresh(assistant_message)

        # --------------------------------------------------
        # 4. MESSAGE START
        # --------------------------------------------------

        yield self._format_sse(
            event=ChatEventType.MESSAGE_START.value,
            data={
                "conversation_id": str(conversation_id),
                "user_message_id": str(user_message.message_id),
                "assistant_message_id": str(assistant_message.message_id),
            },
        )

        full_response = ""

        # --------------------------------------------------
        # 5. RUN LANGGRAPH
        # --------------------------------------------------

        config = {
            "configurable": {
                "thread_id": str(conversation_id),
            },
            "recursion_limit": 25,
        }

        context = GraphContext(
            user_id=str(user_id),
            conversation_id=str(conversation_id),
        )

        try:
            async for chunk in self.chat_graph.astream(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": current_user_text,
                        }
                    ]
                },
                config=config,
                context=context,
                stream_mode=[
                    "messages",
                    "updates",
                ],
                version="v2",
            ):
                # ------------------------------------------
                # LLM TOKEN STREAM
                # ------------------------------------------

                if chunk["type"] == "messages":
                    token, metadata = chunk["data"]

                    text = self._extract_text_content(token.content)

                    if not text:
                        continue

                    full_response += text

                    yield self._format_sse(
                        event=ChatEventType.TOKEN.value,
                        data={
                            "assistant_message_id": str(assistant_message.message_id),
                            "content": {
                                "type": "text",
                                "content": text,
                            },
                            "metadata": metadata,
                        },
                    )

                # ------------------------------------------
                # GRAPH STATE UPDATES
                # ------------------------------------------

                elif chunk["type"] == "updates":
                    update_data = chunk["data"]

                    if "__interrupt__" in update_data:
                        # HITL will use this later.
                        yield self._format_sse(
                            event="interrupt",
                            data={
                                "assistant_message_id": str(
                                    assistant_message.message_id
                                ),
                                "data": str(update_data["__interrupt__"]),
                            },
                        )

            # ------------------------------------------------
            # 6. SAVE FINAL ASSISTANT MESSAGE
            # ------------------------------------------------

            assistant_message.content = [
                {
                    "type": "text",
                    "text": full_response,
                }
            ]

            assistant_message.status = {
                "type": "complete",
                "reason": "stop",
            }

            self.message_repository.update(assistant_message)

            conversation.last_message_id = assistant_message.message_id

            conversation.updated_at = datetime.now(UTC)

            self.conversation_repository.session.commit()

            # ------------------------------------------------
            # 7. COMPLETE EVENT
            # ------------------------------------------------

            yield self._format_sse(
                event=ChatEventType.COMPLETE.value,
                data={
                    "conversation_id": str(conversation_id),
                    "assistant_message_id": str(assistant_message.message_id),
                },
            )

        except asyncio.CancelledError:
            assistant_message.content = [
                {
                    "type": "text",
                    "text": full_response,
                }
            ]

            assistant_message.status = {
                "type": "incomplete",
                "reason": "cancelled",
            }

            self.message_repository.update(assistant_message)

            self.message_repository.session.commit()

            raise

        except Exception as exc:
            assistant_message.content = [
                {
                    "type": "text",
                    "text": full_response,
                }
            ]

            assistant_message.status = {
                "type": "incomplete",
                "reason": "error",
            }

            self.message_repository.update(assistant_message)

            self.message_repository.session.commit()

            yield self._format_sse(
                event=ChatEventType.ERROR.value,
                data={
                    "error": str(exc),
                },
            )

            raise
