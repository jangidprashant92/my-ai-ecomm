from datetime import datetime
from decimal import Decimal

from app.models.order import Order
from app.models.order_payment import OrderPayment
from sqlmodel import Session, func, select


class AnalyticsRepository:
    """Persistence operations for analytical queries."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def count_orders(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """Count orders within an optional date range."""

        statement = select(func.count()).select_from(Order)

        if start_date is not None:
            statement = statement.where(
                Order.order_purchase_timestamp >= start_date,
            )

        if end_date is not None:
            statement = statement.where(
                Order.order_purchase_timestamp < end_date,
            )

        result = self.session.exec(
            statement,
        ).one()

        return int(result)

    def total_spending(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> Decimal:
        """Calculate total payment value within an optional date range."""

        statement = (
            select(
                func.coalesce(
                    func.sum(OrderPayment.payment_value),
                    0,
                )
            )
            .select_from(OrderPayment)
            .join(
                Order,
                Order.order_id == OrderPayment.order_id,
            )
        )

        if start_date is not None:
            statement = statement.where(
                Order.order_purchase_timestamp >= start_date,
            )

        if end_date is not None:
            statement = statement.where(
                Order.order_purchase_timestamp < end_date,
            )

        result = self.session.exec(
            statement,
        ).one()

        return Decimal(result)
