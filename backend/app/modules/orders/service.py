from dataclasses import dataclass

from app.modules.orders.repository import OrderRepository


@dataclass(slots=True)
class OrderQueryService:
    """Provides read-only order queries for application use cases."""

    repository: OrderRepository

    def get_order_status(
        self,
        order_id: str,
    ) -> dict:
        order = self.repository.get_order(
            order_id,
        )

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

    def get_order_products(
        self,
        order_id: str,
    ) -> dict:
        order = self.repository.get_order(
            order_id,
        )

        if order is None:
            return {
                "found": False,
                "order_id": order_id,
                "message": "Order not found.",
            }

        rows = self.repository.get_order_products(
            order_id,
        )

        products = [
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
            for order_item, product in rows
        ]

        return {
            "found": True,
            "order_id": order_id,
            "order_status": order.order_status,
            "products": products,
        }
