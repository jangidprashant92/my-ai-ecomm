from datetime import datetime

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class OrderReview(SQLModel, table=True):

    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    review_id: str = Field(
        index=True,
        max_length=32,
    )

    order_id: str = Field(
        foreign_key="order.order_id",
        index=True,
        max_length=32,
    )

    review_score: int

    review_comment_title: str | None = Field(
        default=None,
        max_length=500,
    )

    review_comment_message: str | None = Field(
        default=None,
        sa_column=Column(Text),
    )

    review_creation_date: datetime

    review_answer_timestamp: datetime | None = Field(
        default=None,
    )