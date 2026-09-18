from dataclasses import dataclass

from app.modules.products.repository import ProductRepository


@dataclass(slots=True)
class ProductQueryService:
    """Provides read-only product queries."""

    repository: ProductRepository

    def get_product(
        self,
        product_id: str,
    ) -> dict:
        """Return product details for a product ID."""

        product = self.repository.get_product(
            product_id=product_id,
        )

        if product is None:
            return {
                "found": False,
                "product_id": product_id,
                "message": "Product not found.",
            }

        return {
            "found": True,
            "product": {
                "product_id": product.product_id,
                "category": product.product_category_name,
                "name_length": product.product_name_lenght,
                "description_length": (product.product_description_lenght),
                "photos_quantity": (product.product_photos_qty),
                "weight_g": product.product_weight_g,
                "length_cm": product.product_length_cm,
                "height_cm": product.product_height_cm,
                "width_cm": product.product_width_cm,
            },
        }
