from typing import Any

from app.ai.graph.state import ChatState, GraphContext
from app.ai.prompts.router import ROUTER_PROMPT
from app.ai.schemas.router import IntentDecision
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from langgraph.runtime import Runtime


class IntentClassifier:
    """Classifies the latest user request."""

    def __init__(
        self,
        model: BaseChatModel,
    ) -> None:
        self.model = model.with_structured_output(
            IntentDecision,
        )

    async def classify(
        self,
        state: ChatState,
        runtime: Runtime[GraphContext],
    ) -> IntentDecision:
        del runtime  # Context will be used by later policies.

        last_message = state["messages"][-1]

        decision = await self.model.ainvoke(
            [
                SystemMessage(
                    content=ROUTER_PROMPT,
                ),
                HumanMessage(
                    content=str(
                        last_message.content,
                    ),
                ),
            ],
        )

        return decision


def create_intent_classifier_node(
    model: BaseChatModel,
):
    classifier = IntentClassifier(
        model=model,
    )

    async def classify_node(
        state: ChatState,
        runtime: Runtime[GraphContext],
    ) -> dict[str, Any]:
        decision = await classifier.classify(
            state,
            runtime,
        )

        return {
            "intent": decision.intent.value,
            "intent_confidence": decision.confidence,
            "intent_reason": decision.reason,
        }

    return classify_node
