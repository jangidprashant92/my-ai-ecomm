from sqlmodel import Field, SQLModel


class Seller(SQLModel, table=True):

    seller_id: str = Field(
        primary_key=True,
        max_length=32,
    )

    seller_zip_code_prefix: int = Field(
        index=True,
    )

    seller_city: str = Field(
        max_length=100,
    )

    seller_state: str = Field(
        max_length=2,
    )