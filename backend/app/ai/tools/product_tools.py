from app.core.database import engine
from app.models.product import Product
from langchain.tools import tool
from sqlmodel import Session, select


@tool
def get_product(product_id: str) -> dict:
    """Get product information using a product ID.

    Use this tool when the user asks about a specific product.

    Args:
        product_id: The OList product ID.
    """

    with Session(engine) as session:
        product = session.exec(
            select(Product).where(Product.product_id == product_id)
        ).first()

        if product is None:
            return {
                "found": False,
                "product_id": product_id,
                "message": "Product not found.",
            }

        return {
            "found": True,
            "product_id": product.product_id,
            "category": product.product_category_name,
            "weight_g": product.product_weight_g,
            "length_cm": product.product_length_cm,
            "height_cm": product.product_height_cm,
            "width_cm": product.product_width_cm,
            "photos": product.product_photos_qty,
        }
