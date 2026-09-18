from app.core.database import engine
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from langchain.tools import tool
from sqlmodel import Session, select


@tool
def get_order_products(order_id: str) -> dict:
    """Get all products purchased in an e-commerce order.

    Use this tool when the user asks for product information
    based on an order ID.

    Args:
        order_id: The OList order ID.
    """

    with Session(engine) as session:
        order = session.get(Order, order_id)

        if order is None:
            return {
                "found": False,
                "order_id": order_id,
                "message": "Order not found.",
            }

        statement = (
            select(OrderItem, Product)
            .join(
                Product,
                Product.product_id == OrderItem.product_id,  # type: ignore
            )
            .where(OrderItem.order_id == order_id)
        )

        rows = session.exec(statement).all()

        if not rows:
            return {
                "found": True,
                "order_id": order_id,
                "products": [],
                "message": "No products found for this order.",
            }

        products = []

        for order_item, product in rows:
            products.append(
                {
                    "product_id": product.product_id,
                    "category": product.product_category_name,
                    "quantity": 1,
                    "price": float(order_item.price),
                    "freight_value": float(order_item.freight_value),
                    "weight_g": product.product_weight_g,
                    "length_cm": product.product_length_cm,
                    "height_cm": product.product_height_cm,
                    "width_cm": product.product_width_cm,
                }
            )

        return {
            "found": True,
            "order_id": order_id,
            "order_status": order.order_status,
            "products": products,
        }
