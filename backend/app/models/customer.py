from sqlmodel import Field, SQLModel


class Customer(SQLModel, table=True):

    customer_id: str = Field(
        primary_key=True,
        max_length=32,
    )

    customer_unique_id: str = Field(
        index=True,
        max_length=32,
    )

    customer_zip_code_prefix: int = Field(
        index=True,
    )

    customer_city: str = Field(
        max_length=100,
    )

    customer_state: str = Field(
        max_length=2,
    )