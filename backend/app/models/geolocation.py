from sqlmodel import Field, SQLModel


class Geolocation(SQLModel, table=True):
    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    geolocation_zip_code_prefix: int = Field(
        index=True,
    )

    geolocation_lat: float

    geolocation_lng: float

    geolocation_city: str = Field(
        max_length=100,
    )

    geolocation_state: str = Field(
        max_length=2,
    )
