"""
Pydantic models for the /ask API.

Pydantic validates incoming requests (shape, types, length)
and serialises outgoing responses (typed, documented in /docs).
"""
from typing import Any

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Natural-language question about the sales data.",
    )


class AskResponse(BaseModel):
    answer: str = Field(..., description="Human-readable answer.")
    intent: str = Field(..., description="Which intent the question was classified as.")
    data: dict[str, Any] = Field(default_factory=dict, description="Primary result values.")
    supporting_table: list[dict[str, Any]] | None = Field(
        default=None, description="Optional breakdown table for ranking intents."
    )