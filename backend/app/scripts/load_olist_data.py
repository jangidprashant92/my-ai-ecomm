from pathlib import Path

from app.models.category_translation import ProductCategoryNameTranslation
from app.models.customer import Customer
from app.models.geolocation import Geolocation
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_payment import OrderPayment
from app.models.order_review import OrderReview
from app.models.product import Product
from app.models.seller import Seller
from app.scripts.ingest import ingest_csv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

DATA_DIR = PROJECT_ROOT / "datasets" / "raw"


def load_olist_data():
 
    # ==================================
    # 1. CATEGORY TRANSLATION
    # ==================================

    ingest_csv(
        csv_path=(f"{DATA_DIR}/product_category_name_translation.csv"),
        model=ProductCategoryNameTranslation,
    )

    # ==================================
    # 2. PRODUCTS
    # ==================================

    ingest_csv(
        csv_path=(f"{DATA_DIR}/olist_products_dataset.csv"),
        model=Product,
    )

    # ==================================
    # 3. CUSTOMERS
    # ==================================

    ingest_csv(
        csv_path=(f"{DATA_DIR}/olist_customers_dataset.csv"),
        model=Customer,
    )

    # ==================================
    # 4. SELLERS
    # ==================================

    ingest_csv(
        csv_path=(f"{DATA_DIR}/olist_sellers_dataset.csv"),
        model=Seller,
    )

    # ==================================
    # 5. GEOLOCATIONS
    # ==================================

    ingest_csv(
        csv_path=(f"{DATA_DIR}/olist_geolocation_dataset.csv"),
        model=Geolocation,
    )

    # ==================================
    # 6. ORDERS
    # ==================================

    ingest_csv(
        csv_path=(f"{DATA_DIR}/olist_orders_dataset.csv"),
        model=Order,
        date_columns=[
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )

    # ==================================
    # 7. ORDER ITEMS
    # ==================================

    ingest_csv(
        csv_path=(f"{DATA_DIR}/olist_order_items_dataset.csv"),
        model=OrderItem,
        date_columns=[
            "shipping_limit_date",
        ],
    )

    # ==================================
    # 8. PAYMENTS
    # ==================================

    ingest_csv(
        csv_path=(f"{DATA_DIR}/olist_order_payments_dataset.csv"),
        model=OrderPayment,
    )

    # ==================================
    # 9. REVIEWS
    # ==================================

    ingest_csv(
        csv_path=(f"{DATA_DIR}/olist_order_reviews_dataset.csv"),
        model=OrderReview,
        date_columns=[
            "review_creation_date",
            "review_answer_timestamp",
        ],
    )


if __name__ == "__main__":
    load_olist_data()
