from app.core.database import create_session
from app.modules.analytics.repository import AnalyticsRepository
from app.modules.analytics.service import AnalyticsQueryService


def main() -> None:
    with create_session() as session:
        repository = AnalyticsRepository(
            session=session,
        )

        service = AnalyticsQueryService(
            repository=repository,
        )

        print("\n=== COUNT ORDERS ===")
        print(
            service.count_orders(),
        )

        print("\n=== TOTAL SPENDING ===")
        print(
            service.total_spending(),
        )

        print("\n=== TOP PRODUCTS ===")
        print(
            service.top_products(
                limit=5,
            ),
        )

        print("\n=== SALES BY CATEGORY ===")
        print(
            service.sales_by_category(),
        )


if __name__ == "__main__":
    main()
