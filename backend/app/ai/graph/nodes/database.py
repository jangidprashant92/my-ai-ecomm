from typing import Any

from app.ai.graph.state import ChatState, GraphContext
from app.ai.prompts.database import DATABASE_QUERY_PROMPT
from app.ai.schemas.database import DatabaseQueryPlan
from langchain_core.language_models import BaseChatModel
from langgraph.runtime import Runtime


class DatabaseQueryPlanner:
    """Creates validated database query plans from user questions."""

    def __init__(
        self,
        model: BaseChatModel,
    ) -> None:
        self.model = model.with_structured_output(
            DatabaseQueryPlan,
        )

    async def create_plan(
        self,
        question: str,
    ) -> DatabaseQueryPlan:

        result = await self.model.ainvoke(
            [
                {
                    "role": "system",
                    "content": DATABASE_QUERY_PROMPT,
                },
                {
                    "role": "user",
                    "content": question,
                },
            ]
        )

        if isinstance(result, DatabaseQueryPlan):
            return result

        if isinstance(result, dict):
            return DatabaseQueryPlan.model_validate(
                result,
            )

        raise TypeError(f"Unexpected database planner result: {type(result).__name__}")


def create_database_planner_node(
    model: BaseChatModel,
):
    planner = DatabaseQueryPlanner(
        model=model,
    )

    async def database_planner_node(
        state: ChatState,
        runtime: Runtime[GraphContext],
    ) -> dict[str, Any]:

        del runtime

        last_message = state["messages"][-1]

        plan = await planner.create_plan(
            str(last_message.content),
        )

        return {
            "database_plan": plan.model_dump(
                mode="json",
            ),
        }

    return database_planner_node
