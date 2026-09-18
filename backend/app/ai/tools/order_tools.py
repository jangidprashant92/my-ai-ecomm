import mlflow
from app.core.database import engine
from app.models.order import Order
from langchain.tools import tool
from sqlmodel import Session, select


@tool
@mlflow.trace(span_type="TOOL", name="get_order_status")
def get_order_status(order_id: str) -> dict:
    """Get the current status and delivery information for an e-commerce order.

    Use this tool when the user asks about a specific order's status,
    delivery state, purchase date, or estimated delivery date.

    Args:
        order_id: The OList order ID.
    """

    with Session(engine) as session:
        order = session.exec(select(Order).where(Order.order_id == order_id)).first()

        print("order=====================================")
        print(order)

        if order is None:
            return {
                "found": False,
                "order_id": order_id,
                "message": "Order not found.",
            }

        return {
            "found": True,
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "status": order.order_status,
            "purchase_date": (
                order.order_purchase_timestamp.isoformat()
                if order.order_purchase_timestamp
                else None
            ),
            "approved_at": (
                order.order_approved_at.isoformat() if order.order_approved_at else None
            ),
            "estimated_delivery": (
                order.order_estimated_delivery_date.isoformat()
                if order.order_estimated_delivery_date
                else None
            ),
            "delivered_at": (
                order.order_delivered_customer_date.isoformat()
                if order.order_delivered_customer_date
                else None
            ),
        }
