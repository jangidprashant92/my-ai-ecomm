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
from app.modules.messages.schemas import ChatEventType, HumanReviewRequest
from app.observability.mlflow_tracer import HITLAwareMlflowTracer
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage
from langgraph.types import Command

USER_VISIBLE_NODES = {
    "general_assistant",
    "database_answer",
    "knowledge_assistant",
    "commerce_agent",
}


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

    def _is_user_visible_model_stream(
        self,
        metadata: dict[str, Any],
    ) -> bool:

        tags = metadata.get("tags", [])

        if "rag_query_rewrite" in tags:
            return False

        node_name = metadata.get("langgraph_node")

        if node_name in USER_VISIBLE_NODES:
            return True

        checkpoint_ns = str(
            metadata.get(
                "langgraph_checkpoint_ns",
                "",
            )
        )

        return "commerce_agent" in checkpoint_ns

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

    def _extract_model_output_text(
        self,
        message: Any,
    ) -> str:
        """
        Return only user-visible assistant text.

        Ignore:
        - reasoning
        - tool calls
        - tool call chunks
        - tool results
        """

        if isinstance(message, ToolMessage):
            return ""

        if not isinstance(
            message,
            (AIMessage, AIMessageChunk),
        ):
            return ""

        # Never stream tool-call messages/chunks.
        if getattr(message, "tool_calls", None):
            return ""

        if getattr(message, "tool_call_chunks", None):
            return ""

        # --------------------------------------------------
        # IMPORTANT:
        # Use normalized content blocks as the source of truth.
        # --------------------------------------------------

        blocks = getattr(message, "content_blocks", None)

        if isinstance(blocks, list):
            text_parts: list[str] = []

            for block in blocks:
                if not isinstance(block, dict):
                    continue

                block_type = block.get("type")

                # Only final/user-visible text
                if block_type != "text":
                    continue

                text = block.get("text")

                if isinstance(text, str) and text:
                    text_parts.append(text)

            return "".join(text_parts)

        # --------------------------------------------------
        # Fallback for providers that return plain content
        # --------------------------------------------------

        content = message.content

        if isinstance(content, str):
            return content

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
            "callbacks": [
                HITLAwareMlflowTracer(),
            ],
        }

        context = GraphContext(
            user_id=str(user_id),
            conversation_id=str(conversation_id),
        )

        interrupted = False
        interrupt_payload: dict[str, Any] | None = None

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

                    if not self._is_user_visible_model_stream(metadata):
                        continue

                    text = self._extract_model_output_text(token)

                    if not text:
                        continue

                    full_response += text

                    yield self._format_sse(
                        event=ChatEventType.TOKEN.value,
                        data={
                            "assistant_message_id": str(
                                assistant_message.message_id,
                            ),
                            "content": text,
                        },
                    )

                # ------------------------------------------
                # GRAPH STATE UPDATES
                # ------------------------------------------

                elif chunk["type"] == "updates":
                    update_data = chunk["data"]

                    knowledge_update = update_data.get("knowledge_assistant")

                    if knowledge_update:
                        rag_sources = knowledge_update.get(
                            "rag_sources",
                            [],
                        )

                        if rag_sources:
                            yield self._format_sse(
                                event=ChatEventType.SOURCES.value,
                                data={
                                    "conversation_id": str(conversation_id),
                                    "assistant_message_id": str(
                                        assistant_message.message_id,
                                    ),
                                    "sources": rag_sources,
                                },
                            )

                    if "__interrupt__" in update_data:
                        interrupted = True

                        interrupt_obj = update_data["__interrupt__"][0]
                        interrupt_value = interrupt_obj.value

                        interrupt_payload = {
                            "action_requests": interrupt_value["action_requests"],
                            "review_configs": interrupt_value["review_configs"],
                        }

                        assistant_message.content = [
                            {
                                "type": "text",
                                "text": "Waiting for human approval.",
                            }
                        ]

                        assistant_message.status = {
                            "type": "waiting_for_approval",
                            "reason": "human_review",
                            "interrupt": interrupt_payload,
                        }

                        self.message_repository.update(
                            assistant_message,
                        )

                        conversation.last_message_id = assistant_message.message_id

                        conversation.updated_at = datetime.now(UTC)

                        self.conversation_repository.session.commit()

                        yield self._format_sse(
                            event=ChatEventType.INTERRUPT.value,
                            data={
                                "conversation_id": str(conversation_id),
                                "assistant_message_id": str(
                                    assistant_message.message_id,
                                ),
                                "data": interrupt_payload,
                            },
                        )

                        continue

            # ------------------------------------------------
            # HITL INTERRUPT
            # ------------------------------------------------

            if interrupted:
                return

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

    async def resume_human_review(
        self,
        conversation_id: uuid.UUID,
        review: HumanReviewRequest,
    ):
        config = {
            "configurable": {
                "thread_id": str(conversation_id),
            },
            "recursion_limit": 25,
            "callbacks": [
                HITLAwareMlflowTracer(),
            ],
        }

        context = GraphContext(
            user_id="12345678-1234-4234-8234-123456789abc",
            conversation_id=str(conversation_id),
        )

        # ---------------------------------------------
        # 1. Find pending assistant message
        # ---------------------------------------------

        assistant_message = await self.message_repository.get_pending_human_review(
            conversation_id=conversation_id,
            assistant_message_id=review.assistant_message_id,
        )

        if assistant_message is None:
            yield self._format_sse(
                event=ChatEventType.ERROR.value,
                data={
                    "error": "No pending human review found.",
                },
            )
            return

        # ---------------------------------------------
        # 2. Build decision
        # ---------------------------------------------

        decision: dict[str, Any] = {
            "type": review.decision.value,
        }

        if review.decision.value == "reject" and review.message:
            decision["message"] = review.message

        resume_command = Command(
            resume={
                "decisions": [
                    decision,
                ],
            },
        )

        # ---------------------------------------------
        # 3. Resume LangGraph
        # ---------------------------------------------

        full_response = ""

        try:
            async for chunk in self.chat_graph.astream(
                resume_command,
                config=config,
                context=context,
                stream_mode=[
                    "messages",
                    "updates",
                ],
                version="v2",
            ):
                if chunk["type"] == "messages":
                    token, metadata = chunk["data"]

                    print(
                        "RESUME METADATA:",
                        {
                            "langgraph_node": metadata.get("langgraph_node"),
                            "langgraph_checkpoint_ns": metadata.get(
                                "langgraph_checkpoint_ns"
                            ),
                        },
                    )

                    if not self._is_user_visible_model_stream(metadata):
                        continue

                    text = self._extract_model_output_text(token)

                    if not text:
                        continue

                    full_response += text

                    yield self._format_sse(
                        event=ChatEventType.TOKEN.value,
                        data={
                            "conversation_id": str(conversation_id),
                            "assistant_message_id": str(
                                assistant_message.message_id,
                            ),
                            "content": text,
                        },
                    )

            # ---------------------------------------------
            # 4. Persist final assistant response
            # ---------------------------------------------

            assistant_message.content = [
                {
                    "type": "text",
                    "text": full_response,
                }
            ]

            assistant_message.status = {
                "type": "complete",
                "reason": "stop",
                "human_review": {
                    "decision": review.decision.value,
                },
            }

            self.message_repository.update(
                assistant_message,
            )

            # ---------------------------------------------
            # 5. Update conversation
            # ---------------------------------------------

            conversation = self.conversation_repository.get(
                conversation_id,
            )

            if conversation:
                conversation.last_message_id = assistant_message.message_id
                conversation.updated_at = datetime.now(UTC)

            self.conversation_repository.session.commit()

            # ---------------------------------------------
            # 6. Tell frontend stream is complete
            # ---------------------------------------------

            yield self._format_sse(
                event=ChatEventType.COMPLETE.value,
                data={
                    "conversation_id": str(
                        conversation_id,
                    ),
                    "assistant_message_id": str(
                        assistant_message.message_id,
                    ),
                    "human_review": {
                        "decision": review.decision.value,
                    },
                },
            )

        except Exception as exc:
            assistant_message.status = {
                "type": "incomplete",
                "reason": "error",
                "human_review": {
                    "decision": review.decision.value,
                },
            }

            self.message_repository.update(
                assistant_message,
            )

            self.message_repository.session.commit()

            yield self._format_sse(
                event=ChatEventType.ERROR.value,
                data={
                    "error": str(exc),
                    "assistant_message_id": str(
                        assistant_message.message_id,
                    ),
                },
            )

            raise
