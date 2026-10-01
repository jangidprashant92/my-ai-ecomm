from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import AgentState
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    RemoveMessage,
    ToolMessage,
)


class StripHistoricalReasoningMiddleware(AgentMiddleware):
    """
    Compact previous conversation turns before the Commerce Agent
    calls the model.

    Rules:

    - Keep previous HumanMessage objects.
    - Keep previous final assistant text.
    - Remove previous assistant tool-call messages.
    - Remove previous ToolMessage objects.
    - Remove reasoning blocks from previous assistant messages.
    - NEVER modify messages belonging to the current active turn.

    The current active turn is everything after the latest HumanMessage.
    This is important for HITL resume because the pending tool call must
    remain intact.
    """

    @property
    def name(self) -> str:
        return "strip_historical_reasoning"

    def before_model(
        self,
        state: AgentState[Any],
        runtime: Any,
    ) -> dict[str, Any] | None:

        messages = state.get("messages", [])

        if not messages:
            return None

        # --------------------------------------------------
        # Find the latest user message.
        #
        # Everything AFTER this message belongs to the
        # currently active turn and must remain untouched.
        # --------------------------------------------------

        latest_user_index = -1

        for index in range(len(messages) - 1, -1, -1):
            if isinstance(messages[index], HumanMessage):
                latest_user_index = index
                break

        if latest_user_index <= 0:
            return None

        updates: list[Any] = []

        # --------------------------------------------------
        # Compact only previous turns.
        # --------------------------------------------------

        for message in messages[:latest_user_index]:
            # ------------------------------------------------
            # Previous tool result
            #
            # We do not need old ToolMessage objects once the
            # previous turn is finished.
            # ------------------------------------------------

            if isinstance(message, ToolMessage):
                if message.id:
                    updates.append(
                        RemoveMessage(
                            id=message.id,
                        )
                    )

                continue

            # ------------------------------------------------
            # Previous assistant message
            # ------------------------------------------------

            if isinstance(message, AIMessage):
                # Old tool-call assistant messages are removed.
                #
                # Example:
                #
                # AIMessage(
                #   tool_calls=[request_refund(...)]
                # )
                #
                # The previous final natural-language answer is
                # enough for the next turn.
                # ------------------------------------------------

                if getattr(message, "tool_calls", None):
                    if message.id:
                        updates.append(
                            RemoveMessage(
                                id=message.id,
                            )
                        )

                    continue

                # ------------------------------------------------
                # Keep only user-visible text.
                #
                # message.text extracts text blocks and ignores
                # reasoning/tool blocks.
                # ------------------------------------------------

                text = getattr(message, "text", "")

                if isinstance(text, str) and text:
                    updates.append(
                        AIMessage(
                            id=message.id,
                            content=text,
                        )
                    )

                elif message.id:
                    # Nothing user-visible remains.
                    updates.append(
                        RemoveMessage(
                            id=message.id,
                        )
                    )

        if not updates:
            return None

        return {
            "messages": updates,
        }
