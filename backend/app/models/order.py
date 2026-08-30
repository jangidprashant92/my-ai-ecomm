from datetime import datetime

from sqlmodel import Field, SQLModel


class Order(SQLModel, table=True):
    order_id: str = Field(
        primary_key=True,
        max_length=32,
    )

    customer_id: str = Field(
        foreign_key="customer.customer_id",
        index=True,
        max_length=32,
    )

    order_status: str = Field(
        index=True,
        max_length=30,
    )

    order_purchase_timestamp: datetime

    order_approved_at: datetime | None = Field(
        default=None,
    )

    order_delivered_carrier_date: datetime | None = Field(
        default=None,
    )

    order_delivered_customer_date: datetime | None = Field(
        default=None,
    )

    order_estimated_delivery_date: datetime
