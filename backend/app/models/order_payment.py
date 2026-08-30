from decimal import Decimal

from sqlmodel import Field, SQLModel


class OrderPayment(SQLModel, table=True):

    order_id: str = Field(
        foreign_key="order.order_id",
        primary_key=True,
        max_length=32,
    )

    payment_sequential: int = Field(
        primary_key=True,
    )

    payment_type: str = Field(
        max_length=50,
    )

    payment_installments: int

    payment_value: Decimal = Field(
        max_digits=12,
        decimal_places=2,
    )