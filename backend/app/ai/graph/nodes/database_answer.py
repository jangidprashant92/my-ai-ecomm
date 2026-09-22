from typing import Any

from app.ai.graph.state import ChatState, GraphContext
from langchain.messages import SystemMessage
from langchain_core.language_models import BaseChatModel
from langgraph.runtime import Runtime


class DatabaseAnswerGenerator:
    """Generates a natural-language answer from database results."""

    def __init__(
        self,
        model: BaseChatModel,
    ) -> None:
        self.model = model

    async def generate(
        self,
        question: str,
        result: dict[str, Any],
    ) -> str:

        response = await self.model.ainvoke(
            [
                SystemMessage(
                    content=(
                        "You are an e-commerce analytics assistant. "
                        "Answer the user's question using only the "
                        "provided database result. Do not invent "
                        "numbers or facts."
                    ),
                ),
                {
                    "role": "user",
                    "content": (f"Question:\n{question}\n\nDatabase result:\n{result}"),
                },
            ]
        )

        return str(response.content)


def create_database_answer_node(
    model: BaseChatModel,
):
    generator = DatabaseAnswerGenerator(
        model=model,
    )

    async def database_answer_node(
        state: ChatState,
        runtime: Runtime[GraphContext],
    ) -> dict[str, Any]:

        del runtime

        last_message = state["messages"][-1]

        result = state.get(
            "database_result",
        )

        if result is None:
            raise ValueError(
                "Database result is missing.",
            )

        answer = await generator.generate(
            question=str(
                last_message.content,
            ),
            result=result,
        )

        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": answer,
                }
            ],
        }

    return database_answer_node
