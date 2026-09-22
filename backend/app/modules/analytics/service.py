from dataclasses import dataclass
from datetime import datetime

from app.modules.analytics.repository import AnalyticsRepository


@dataclass(slots=True)
class AnalyticsQueryService:
    """Application service for analytical database queries."""

    repository: AnalyticsRepository

    def count_orders(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict:
        """Count orders within an optional date range."""

        count = self.repository.count_orders(
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "metric": "order_count",
            "value": count,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }

    def total_spending(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict:
        """Calculate total spending within a date range."""

        total = self.repository.total_spending(
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "metric": "total_spending",
            "value": str(total),
            "start_date": (start_date.isoformat() if start_date else None),
            "end_date": (end_date.isoformat() if end_date else None),
            "currency": "BRL",
        }
