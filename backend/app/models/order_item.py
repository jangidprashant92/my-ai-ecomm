from datetime import datetime
from decimal import Decimal

from sqlmodel import Field, SQLModel


class OrderItem(SQLModel, table=True):
    order_id: str = Field(
        foreign_key="order.order_id",
        primary_key=True,
        max_length=32,
    )

    order_item_id: int = Field(
        primary_key=True,
    )

    product_id: str = Field(
        foreign_key="product.product_id",
        index=True,
        max_length=32,
    )

    seller_id: str = Field(
        foreign_key="seller.seller_id",
        index=True,
        max_length=32,
    )

    shipping_limit_date: datetime

    price: Decimal = Field(
        max_digits=12,
        decimal_places=2,
    )

    freight_value: Decimal = Field(
        max_digits=12,
        decimal_places=2,
    )
