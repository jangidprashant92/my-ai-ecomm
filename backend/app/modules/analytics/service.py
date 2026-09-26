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
        total = self.repository.total_spending(
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "metric": "total_spending",
            "value": str(total),
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "currency": "BRL",
        }

    def top_products(
        self,
        limit: int = 10,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict:
        products = self.repository.top_products(
            limit=limit,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "metric": "top_products",
            "value": products,
            "limit": limit,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "currency": "BRL",
        }

    def sales_by_category(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict:
        categories = self.repository.sales_by_category(
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "metric": "sales_by_category",
            "value": categories,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "currency": "BRL",
        }
