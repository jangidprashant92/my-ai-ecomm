from enum import StrEnum

from pydantic import BaseModel, Field


class Intent(StrEnum):
    """Supported top-level user intents."""

    GENERAL = "general"
    ORDER = "order"
    PRODUCT = "product"


class IntentDecision(BaseModel):
    """Structured classification result used for graph routing."""

    intent: Intent = Field(
        description="The user's primary intent.",
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1.",
    )

    reason: str = Field(
        min_length=1,
        description="Short explanation for the selected intent.",
    )
