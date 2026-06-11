"""Structured exceptions for the core model package."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModelValidationError(ValueError):
    """Validation error with machine-readable context.

    Args:
        code: Stable error code for callers and tests.
        message: Human-readable explanation of the validation failure.
        path: Optional model path where validation failed.
        details: Extra structured context for diagnostics.
    """

    code: str
    message: str
    path: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Return an actionable error message."""
        location = f" at {self.path}" if self.path else ""
        return f"{self.code}{location}: {self.message}"

