from app.ai.tools.get_order_products import get_order_products
from app.ai.tools.order_tools import get_order_status
from app.ai.tools.product_tools import get_product

ALL_TOOLS = [
    get_order_status,
    get_product,
    get_order_products,
]
