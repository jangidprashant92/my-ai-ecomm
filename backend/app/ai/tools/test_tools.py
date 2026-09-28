from langchain_core.tools import tool

_attempt_count = 0


@tool
def test_write_operation() -> str:
    """
    Temporary tool used to test authorization guardrails.

    This tool simulates a write operation such as refunding,
    cancelling, or updating an order.
    """
    print("[TEST WRITE] TOOL EXECUTED")

    return "TEST WRITE OPERATION EXECUTED"


@tool
def flaky_test_tool() -> str:
    """
    Temporary tool used to test ToolRetryMiddleware.

    The first two attempts fail.
    The third attempt succeeds.
    """
    global _attempt_count

    _attempt_count += 1

    print(f"[FLAKY TOOL] attempt={_attempt_count}")

    if _attempt_count < 3:
        raise ConnectionError("Simulated temporary connection failure.")

    return "Flaky tool succeeded after retrying."
