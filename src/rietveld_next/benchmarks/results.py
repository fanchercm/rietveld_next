"""Machine-readable benchmark result records."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any


@dataclass(frozen=True)
class BenchmarkTiming:
    """Runtime statistics in seconds.

    Args:
        median_seconds: Median steady-state runtime in seconds.
        min_seconds: Minimum steady-state runtime in seconds.
        max_seconds: Maximum steady-state runtime in seconds.
        compile_seconds: Optional one-time compile or setup time in seconds.
    """

    median_seconds: float
    min_seconds: float
    max_seconds: float
    compile_seconds: float | None = None

    def __post_init__(self) -> None:
        """Validate finite, non-negative timing values."""
        _finite_nonnegative(self.median_seconds, "timing.median_seconds")
        _finite_nonnegative(self.min_seconds, "timing.min_seconds")
        _finite_nonnegative(self.max_seconds, "timing.max_seconds")
        if self.compile_seconds is not None:
            _finite_nonnegative(self.compile_seconds, "timing.compile_seconds")
        if self.min_seconds > self.median_seconds or self.median_seconds > self.max_seconds:
            raise ValueError("timing values must satisfy min_seconds <= median_seconds <= max_seconds.")

    def to_dict(self) -> dict[str, float | None]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "median_seconds": self.median_seconds,
            "min_seconds": self.min_seconds,
            "max_seconds": self.max_seconds,
            "compile_seconds": self.compile_seconds,
        }


@dataclass(frozen=True)
class BenchmarkResult:
    """Benchmark output record shared by Python, JAX, and Rust-style runners.

    Args:
        name: Stable benchmark name.
        backend: Backend label, such as ``"python"``, ``"jax"``, or ``"rust"``.
        status: ``"ok"`` or ``"skipped"``.
        dtype: Numeric dtype used by the benchmark.
        input_size: Number of axis samples or equivalent problem size.
        iterations: Number of measured iterations.
        warmup: Number of warmup iterations.
        checksum: Deterministic numerical checksum, when available.
        timing: Runtime statistics, when the benchmark ran.
        environment: Reproducibility metadata such as device and versions.
        skip_reason: Human-readable reason when ``status`` is ``"skipped"``.
    """

    name: str
    backend: str
    status: str
    dtype: str
    input_size: int
    iterations: int
    warmup: int
    checksum: float | None
    timing: BenchmarkTiming | None = None
    environment: dict[str, Any] = field(default_factory=dict)
    skip_reason: str | None = None

    def __post_init__(self) -> None:
        """Validate benchmark result shape and skip policy."""
        _non_empty_text(self.name, "name")
        _non_empty_text(self.backend, "backend")
        _non_empty_text(self.dtype, "dtype")
        if self.status not in {"ok", "skipped"}:
            raise ValueError(f"status must be 'ok' or 'skipped', got {self.status!r}.")
        if self.status == "ok" and self.timing is None:
            raise ValueError("timing is required for completed benchmark results.")
        if self.status == "skipped" and not self.skip_reason:
            raise ValueError("skip_reason is required for skipped benchmark results.")
        if isinstance(self.input_size, bool) or not isinstance(self.input_size, int) or self.input_size < 0:
            raise ValueError(f"input_size must be non-negative, got {self.input_size!r}.")
        if isinstance(self.iterations, bool) or not isinstance(self.iterations, int) or self.iterations < 0:
            raise ValueError(f"iterations must be non-negative, got {self.iterations!r}.")
        if isinstance(self.warmup, bool) or not isinstance(self.warmup, int) or self.warmup < 0:
            raise ValueError(f"warmup must be non-negative, got {self.warmup!r}.")
        if self.checksum is not None:
            _finite_float(self.checksum, "checksum")
        _json_compatible(self.environment, "environment")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "name": self.name,
            "backend": self.backend,
            "status": self.status,
            "dtype": self.dtype,
            "input_size": self.input_size,
            "iterations": self.iterations,
            "warmup": self.warmup,
            "checksum": self.checksum,
            "timing": None if self.timing is None else self.timing.to_dict(),
            "environment": dict(sorted(self.environment.items())),
            "skip_reason": self.skip_reason,
        }


def skipped_benchmark(
    *,
    name: str,
    backend: str,
    dtype: str,
    input_size: int,
    reason: str,
) -> BenchmarkResult:
    """Create a machine-readable skipped benchmark result.

    Args:
        name: Stable benchmark name.
        backend: Backend label.
        dtype: Intended numeric dtype.
        input_size: Intended input size.
        reason: Human-readable skip reason.

    Returns:
        A validated skipped :class:`BenchmarkResult`.
    """
    return BenchmarkResult(
        name=name,
        backend=backend,
        status="skipped",
        dtype=dtype,
        input_size=input_size,
        iterations=0,
        warmup=0,
        checksum=None,
        timing=None,
        environment={},
        skip_reason=reason,
    )


def _non_empty_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string.")


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _finite_nonnegative(value: float, name: str) -> float:
    number = _finite_float(value, name)
    if number < 0.0:
        raise ValueError(f"{name} must be non-negative, got {number!r}.")
    return number


def _json_compatible(value: Any, name: str) -> None:
    if value is None or isinstance(value, str | bool):
        return
    if isinstance(value, int | float) and not isinstance(value, bool):
        _finite_float(value, name)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _json_compatible(item, f"{name}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{name} keys must be strings, got {key!r}.")
            _json_compatible(item, f"{name}.{key}")
        return
    raise ValueError(f"{name} must be JSON-compatible, got {value!r}.")
