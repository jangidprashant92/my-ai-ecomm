from app.ai.schemas.database import DatabaseOperation


class DatabaseCapabilityPolicy:
    """Defines which analytical operations the database supports."""

    SUPPORTED_OPERATIONS = frozenset(
        {
            DatabaseOperation.COUNT_ORDERS,
            DatabaseOperation.TOTAL_SPENDING,
            DatabaseOperation.TOP_PRODUCTS,
            DatabaseOperation.SALES_BY_CATEGORY,
            DatabaseOperation.UNSUPPORTED,
        }
    )

    @classmethod
    def is_supported(
        cls,
        operation: DatabaseOperation,
    ) -> bool:
        return operation in cls.SUPPORTED_OPERATIONS
