from decimal import Decimal

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class RefundRequest(BaseModel):
    """Arguments required to request a refund."""

    order_id: str = Field(
        min_length=32,
        max_length=32,
        description="32-character order ID.",
    )

    amount: Decimal = Field(
        gt=0,
        description="Refund amount in BRL.",
    )

    reason: str = Field(
        min_length=3,
        max_length=500,
        description="Reason for requesting the refund.",
    )


@tool(args_schema=RefundRequest)
def request_refund(
    order_id: str,
    amount: Decimal,
    reason: str,
) -> dict:
    """
    Request a refund for an order.

    This is currently a dry-run operation.
    It does not modify the database.
    """

    print(
        "[REFUND TOOL] Executing refund request:",
        order_id,
        amount,
        reason,
    )

    return {
        "status": "refund_requested",
        "order_id": order_id,
        "amount": str(amount),
        "currency": "BRL",
        "reason": reason,
        "execution_mode": "dry_run",
    }
