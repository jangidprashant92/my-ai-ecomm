from datetime import date
from typing import Any

from app.ai.graph.state import ChatState, GraphContext
from app.ai.schemas.database import (
    DatabaseQueryPlan,
    TimeScope,
)
from langgraph.runtime import Runtime


class DatabaseTemporalResolver:
    """Resolve a database query's temporal scope deterministically."""

    def resolve(
        self,
        plan: DatabaseQueryPlan,
    ) -> tuple[date | None, date | None]:
        """Resolve the query into an inclusive start/exclusive end date range."""

        temporal = plan.temporal

        # ----------------------------------------------
        # ALL TIME
        # ----------------------------------------------

        if temporal.scope == TimeScope.ALL_TIME:
            return None, None

        # ----------------------------------------------
        # EXPLICIT YEAR
        # ----------------------------------------------

        if temporal.scope == TimeScope.YEAR and temporal.year is not None:
            return (
                date(
                    temporal.year,
                    1,
                    1,
                ),
                date(
                    temporal.year + 1,
                    1,
                    1,
                ),
            )

        # ----------------------------------------------
        # MONTH
        #
        # No year → current calendar year
        # ----------------------------------------------

        if temporal.scope == TimeScope.MONTH and temporal.month is not None:
            year = temporal.year if temporal.year is not None else date.today().year  # noqa: DTZ011

            return self._resolve_month(
                year=year,
                month=temporal.month,
            )

        # ----------------------------------------------
        # EXPLICIT DATE RANGE
        # ----------------------------------------------

        if temporal.scope == TimeScope.DATE_RANGE:
            if temporal.start_date is None or temporal.end_date is None:
                raise ValueError(
                    "Date range is incomplete.",
                )

            return (
                temporal.start_date,
                temporal.end_date,
            )

        raise ValueError(
            "Unable to resolve database temporal scope.",
        )

    @staticmethod
    def _resolve_month(
        year: int,
        month: int,
    ) -> tuple[date, date]:
        """Return [month_start, next_month_start)."""

        start_date = date(
            year,
            month,
            1,
        )

        if month == 12:
            end_date = date(
                year + 1,
                1,
                1,
            )
        else:
            end_date = date(
                year,
                month + 1,
                1,
            )

        return start_date, end_date


def create_database_time_resolver_node():
    resolver = DatabaseTemporalResolver()

    async def database_time_resolver_node(
        state: ChatState,
        runtime: Runtime[GraphContext],
    ) -> dict[str, Any]:

        del runtime

        raw_plan = state.get("database_plan")

        if raw_plan is None:
            raise ValueError(
                "Database query plan is missing.",
            )

        plan = DatabaseQueryPlan.model_validate(
            raw_plan,
        )

        start_date, end_date = resolver.resolve(
            plan,
        )

        return {
            "database_time_resolved": True,
            "database_start_date": start_date,
            "database_end_date": end_date,
        }

    return database_time_resolver_node
