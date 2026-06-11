"""Deterministic retry and backoff policy."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from rietveld_next.hpc.scheduler import JobResult


@dataclass(frozen=True)
class RetryBackoffPolicy:
    """Retry policy with deterministic exponential backoff.

    Args:
        max_attempts: Total attempts including the initial attempt.
        initial_delay_seconds: Delay before the first retry.
        multiplier: Backoff multiplier applied after each failed attempt.
        max_delay_seconds: Upper bound for any computed delay.
        retry_statuses: Job statuses eligible for retry.

    Raises:
        ValueError: If timing or attempt limits are invalid.
    """

    max_attempts: int = 3
    initial_delay_seconds: float = 1.0
    multiplier: float = 2.0
    max_delay_seconds: float = 60.0
    retry_statuses: tuple[str, ...] = ("error",)

    def __post_init__(self) -> None:
        if isinstance(self.max_attempts, bool) or self.max_attempts < 1:
            raise ValueError("max_attempts must be a positive integer")
        _finite_nonnegative(self.initial_delay_seconds, "initial_delay_seconds")
        _finite_nonnegative(self.max_delay_seconds, "max_delay_seconds")
        if not math.isfinite(self.multiplier) or self.multiplier < 1.0:
            raise ValueError("multiplier must be finite and at least 1.0")
        if self.initial_delay_seconds > self.max_delay_seconds:
            raise ValueError("initial_delay_seconds must be <= max_delay_seconds")
        if not self.retry_statuses or any(not status for status in self.retry_statuses):
            raise ValueError("retry_statuses must contain non-empty statuses")
        object.__setattr__(self, "retry_statuses", tuple(self.retry_statuses))

    def should_retry(self, result: JobResult, *, attempt_index: int) -> bool:
        """Return whether a result should be retried after an attempt."""

        if attempt_index < 0:
            raise ValueError("attempt_index must be non-negative")
        return result.status in self.retry_statuses and attempt_index + 1 < self.max_attempts

    def delay_for_attempt(self, attempt_index: int) -> float:
        """Return delay before retrying after an attempt."""

        if attempt_index < 0:
            raise ValueError("attempt_index must be non-negative")
        delay = self.initial_delay_seconds * (self.multiplier**attempt_index)
        return min(delay, self.max_delay_seconds)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible policy mapping."""

        return {
            "max_attempts": self.max_attempts,
            "initial_delay_seconds": self.initial_delay_seconds,
            "multiplier": self.multiplier,
            "max_delay_seconds": self.max_delay_seconds,
            "retry_statuses": list(self.retry_statuses),
        }


def _finite_nonnegative(value: float, field_name: str) -> None:
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{field_name} must be finite and non-negative")
