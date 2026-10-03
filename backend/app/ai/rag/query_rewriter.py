from __future__ import annotations

from collections.abc import Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)

QUERY_REWRITE_PROMPT = """
You are a query rewriter for the CommerceOps knowledge base.

Your task is to rewrite the user's latest question into a
standalone search query for vector retrieval.

Rules:

1. Use conversation history to resolve references such as:
   - it
   - that
   - this
   - they
   - them
   - there
   - how long
   - when
   - what about it
   - that rule
   - the same rule

2. Preserve the user's exact intent.

3. If the user refers to a rule from a previous message,
   explicitly include what that rule refers to.

4. If the user compares or relates two policies, explicitly
   mention BOTH policy concepts in the rewritten query.

5. Do not answer the question.

6. Do not invent information.

7. If the user's question is already standalone, return it
   unchanged.

8. Return only the standalone search query.

Example:

Conversation:
User: What is the refund policy for damaged products?
Assistant: Damaged products can be refunded within 7 days.
User: How long can I request it?

Rewritten query:
How long after delivery can I request a refund for a damaged product?

Example:

Conversation:
User: What is the refund policy for damaged products?
Assistant: Damaged-product refunds are allowed within 7 days.
User: What about standard returns?
Assistant: Standard returns are allowed within 30 days.
User: Does the 7-day rule also apply to standard returns?

Rewritten query:
Does the 7-day refund period for damaged products also apply
to the standard return policy?
"""


class ContextualQueryRewriter:
    """Rewrites follow-up questions into standalone retrieval queries."""

    def __init__(
        self,
        model: BaseChatModel,
    ) -> None:
        self.model = model

    async def rewrite(
        self,
        query: str,
        history: Sequence[BaseMessage],
    ) -> str:

        # No history means this is already a standalone query.
        if not history:
            return query

        conversation = self._format_history(
            history=history,
        )

        response = await self.model.ainvoke(
            [
                SystemMessage(
                    content=QUERY_REWRITE_PROMPT,
                ),
                HumanMessage(
                    content=(
                        f"Conversation History:\n"
                        f"{conversation}\n\n"
                        f"Latest User Question:\n"
                        f"{query}"
                    ),
                ),
            ],
            config={
                "tags": ["rag_query_rewrite"],
                "run_name": "rag_query_rewrite",
            },
        )

        rewritten_query = self._extract_text(
            response,
        )

        return rewritten_query or query

    def rewrite_sync(
        self,
        query: str,
        history: Sequence[BaseMessage],
    ) -> str:

        if not history:
            return query

        conversation = self._format_history(
            history=history,
        )

        response = self.model.invoke(
            [
                SystemMessage(
                    content=QUERY_REWRITE_PROMPT,
                ),
                HumanMessage(
                    content=(
                        f"Conversation History:\n"
                        f"{conversation}\n\n"
                        f"Latest User Question:\n"
                        f"{query}"
                    ),
                ),
            ],
            config={
                "tags": ["rag_query_rewrite"],
                "run_name": "rag_query_rewrite",
            },
        )

        rewritten_query = self._extract_text(response)

        return rewritten_query or query

    def _format_history(
        self,
        history: Sequence[BaseMessage],
    ) -> str:

        # Only use the most recent messages.
        recent_messages = list(history)[-6:]

        lines: list[str] = []

        for message in recent_messages:
            if isinstance(message, HumanMessage):
                text = self._extract_message_text(
                    message,
                )

                if text:
                    lines.append(
                        f"User: {text}",
                    )

            elif isinstance(message, AIMessage):
                # Ignore old tool-call messages.
                if getattr(
                    message,
                    "tool_calls",
                    None,
                ):
                    continue

                text = self._extract_message_text(
                    message,
                )

                if text:
                    lines.append(
                        f"Assistant: {text}",
                    )

        return "\n".join(lines)

    @staticmethod
    def _extract_message_text(
        message: BaseMessage,
    ) -> str:

        text = getattr(
            message,
            "text",
            None,
        )

        if isinstance(text, str) and text:
            return text

        content = getattr(
            message,
            "content",
            None,
        )

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts: list[str] = []

            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                    continue

                if not isinstance(block, dict):
                    continue

                if block.get("type") not in {
                    "text",
                    "output_text",
                }:
                    continue

                value = block.get("text")

                if isinstance(value, str):
                    parts.append(value)

            return "".join(parts)

        return ""

    @staticmethod
    def _extract_text(
        message: BaseMessage,
    ) -> str:

        text = getattr(
            message,
            "text",
            None,
        )

        if isinstance(text, str) and text:
            return text.strip()

        content = getattr(
            message,
            "content",
            None,
        )

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            parts: list[str] = []

            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                    continue

                if not isinstance(block, dict):
                    continue

                if block.get("type") not in {
                    "text",
                    "output_text",
                }:
                    continue

                value = block.get("text")

                if isinstance(value, str):
                    parts.append(value)

            return "".join(parts).strip()

        return ""
