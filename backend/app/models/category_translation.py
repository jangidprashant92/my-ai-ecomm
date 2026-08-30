from sqlmodel import Field, SQLModel


class ProductCategoryNameTranslation(SQLModel, table=True):

    product_category_name: str = Field(
        primary_key=True,
        max_length=100,
    )

    product_category_name_english: str = Field(
        max_length=100,
    )