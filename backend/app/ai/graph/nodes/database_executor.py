from collections.abc import Callable
from datetime import date, datetime, time
from typing import Any

from app.ai.graph.state import ChatState, GraphContext
from app.ai.schemas.database import (
    DatabaseOperation,
    DatabaseQueryPlan,
)
from app.modules.analytics.repository import AnalyticsRepository
from app.modules.analytics.service import AnalyticsQueryService
from langgraph.runtime import Runtime
from sqlmodel import Session


class DatabaseQueryExecutor:
    """Execute validated database query plans."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
    ) -> None:
        self.session_factory = session_factory

    @staticmethod
    def _to_datetime(
        value: date | None,
    ) -> datetime | None:
        if value is None:
            return None

        return datetime.combine(
            value,
            time.min,
        )

    def execute(
        self,
        plan: DatabaseQueryPlan,
        start_date: date | None,
        end_date: date | None,
    ) -> dict[str, Any]:
        """Execute a supported read-only database operation."""

        start_datetime = self._to_datetime(start_date)
        end_datetime = self._to_datetime(end_date)

        if plan.operation == DatabaseOperation.UNSUPPORTED:
            return {
                "status": "unsupported",
                "message": (
                    plan.reason or "This operation is not currently supported."
                ),
            }

        with self.session_factory() as session:
            repository = AnalyticsRepository(
                session=session,
            )

            service = AnalyticsQueryService(
                repository=repository,
            )

            if plan.operation == DatabaseOperation.COUNT_ORDERS:
                return service.count_orders(
                    start_date=start_datetime,
                    end_date=end_datetime,
                )

            if plan.operation == DatabaseOperation.TOTAL_SPENDING:
                return service.total_spending(
                    start_date=start_datetime,
                    end_date=end_datetime,
                )

            if plan.operation == DatabaseOperation.TOP_PRODUCTS:
                return service.top_products(
                    limit=plan.limit or 10,
                    start_date=start_datetime,
                    end_date=end_datetime,
                )

            if plan.operation == DatabaseOperation.SALES_BY_CATEGORY:
                return service.sales_by_category(
                    start_date=start_datetime,
                    end_date=end_datetime,
                )

            raise ValueError(f"Unsupported database operation: {plan.operation.value}")


def create_database_executor_node(
    session_factory: Callable[[], Session],
):
    executor = DatabaseQueryExecutor(
        session_factory=session_factory,
    )

    async def database_executor_node(
        state: ChatState,
        runtime: Runtime[GraphContext],
    ) -> dict[str, Any]:

        del runtime

        raw_plan = state.get(
            "database_plan",
        )

        if raw_plan is None:
            raise ValueError(
                "Database query plan is missing.",
            )

        plan = DatabaseQueryPlan.model_validate(
            raw_plan,
        )

        start_date = state.get(
            "database_start_date",
        )

        end_date = state.get(
            "database_end_date",
        )

        if plan.temporal.scope.value != "all_time" and (
            start_date is None or end_date is None
        ):
            raise ValueError(
                "Database temporal scope has not been resolved.",
            )

        result = executor.execute(
            plan=plan,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "database_result": result,
        }

    return database_executor_node
