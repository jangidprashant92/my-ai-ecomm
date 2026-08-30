
from sqlmodel import Field, SQLModel


class Product(SQLModel, table=True):

    product_id: str = Field(
        primary_key=True,
        max_length=32,
    )

    product_category_name: str | None = Field(
        default=None,
        index=True,
        max_length=100,
    )

    product_name_lenght: int | None = Field(
        default=None,
    )

    product_description_lenght: int | None = Field(
        default=None,
    )

    product_photos_qty: int | None = Field(
        default=None,
    )

    product_weight_g: int | None = Field(
        default=None,
    )

    product_length_cm: int | None = Field(
        default=None,
    )

    product_height_cm: int | None = Field(
        default=None,
    )

    product_width_cm: int | None = Field(
        default=None,
    )