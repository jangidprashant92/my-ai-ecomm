from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class DatabaseOperation(StrEnum):
    """Supported read-only analytical operations."""

    COUNT_ORDERS = "count_orders"
    TOTAL_SPENDING = "total_spending"
    TOP_PRODUCTS = "top_products"
    SALES_BY_CATEGORY = "sales_by_category"


class TimeScope(StrEnum):
    """Supported temporal expressions."""

    ALL_TIME = "all_time"
    YEAR = "year"
    MONTH = "month"
    DATE_RANGE = "date_range"


class TemporalFilter(BaseModel):
    """User's requested time scope before resolution."""

    scope: TimeScope = TimeScope.ALL_TIME

    year: int | None = Field(
        default=None,
        description=(
            "Explicit year mentioned by the user. "
            "Never infer a year when the user did not provide one."
        ),
    )

    month: int | None = Field(
        default=None,
        ge=1,
        le=12,
        description=(
            "Month number from 1 to 12 when the user mentions a specific month."
        ),
    )

    start_date: date | None = Field(
        default=None,
        description=(
            "Explicit start date only when the user provides an actual date range."
        ),
    )

    end_date: date | None = Field(
        default=None,
        description=(
            "Explicit exclusive end date only when the user "
            "provides an actual date range."
        ),
    )


class DatabaseQueryPlan(BaseModel):
    """Validated database query plan."""

    operation: DatabaseOperation

    temporal: TemporalFilter = Field(
        default_factory=TemporalFilter,
    )

    limit: int | None = Field(
        default=None,
        ge=1,
        le=100,
    )
