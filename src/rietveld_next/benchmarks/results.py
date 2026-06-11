"""Machine-readable benchmark result records and schema helpers."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import math
from typing import Any


BENCHMARK_RESULT_SCHEMA_VERSION = "benchmark-result-v1"


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
        memory_peak_bytes: Optional peak resident or device memory in bytes.
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
    memory_peak_bytes: int | None = None
    schema_version: str = field(default=BENCHMARK_RESULT_SCHEMA_VERSION, init=False)

    def __post_init__(self) -> None:
        """Validate benchmark result shape and skip policy."""
        _non_empty_text(self.schema_version, "schema_version")
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
        if self.memory_peak_bytes is not None and (
            isinstance(self.memory_peak_bytes, bool)
            or not isinstance(self.memory_peak_bytes, int)
            or self.memory_peak_bytes < 0
        ):
            raise ValueError(f"memory_peak_bytes must be a non-negative integer or None, got {self.memory_peak_bytes!r}.")
        _json_compatible(self.environment, "environment")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "schema_version": self.schema_version,
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
            "memory_peak_bytes": self.memory_peak_bytes,
        }


def skipped_benchmark(
    *,
    name: str,
    backend: str,
    dtype: str,
    input_size: int,
    reason: str,
    iterations: int = 0,
    warmup: int = 0,
    environment: dict[str, Any] | None = None,
) -> BenchmarkResult:
    """Create a machine-readable skipped benchmark result.

    Args:
        name: Stable benchmark name.
        backend: Backend label.
        dtype: Intended numeric dtype.
        input_size: Intended input size.
        reason: Human-readable skip reason.
        iterations: Requested measured iteration count.
        warmup: Requested warmup iteration count.
        environment: Optional reproducibility metadata.

    Returns:
        A validated skipped :class:`BenchmarkResult`.
    """
    return BenchmarkResult(
        name=name,
        backend=backend,
        status="skipped",
        dtype=dtype,
        input_size=input_size,
        iterations=iterations,
        warmup=warmup,
        checksum=None,
        timing=None,
        environment={} if environment is None else environment,
        skip_reason=reason,
    )


def benchmark_result_schema() -> dict[str, Any]:
    """Return the dependency-free benchmark result schema draft.

    The returned mapping intentionally mirrors a JSON Schema document without
    requiring a runtime JSON Schema dependency. It documents fields shared by
    Python, JAX, and Rust-style benchmark producers.

    Returns:
        A JSON-compatible schema-like dictionary.

    Example:
        >>> schema = benchmark_result_schema()
        >>> schema["required"][0]
        'schema_version'
    """
    return deepcopy(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://rietveld-next.local/schemas/benchmark-result-v1",
            "title": "Rietveld Next benchmark result",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "schema_version",
                "name",
                "backend",
                "status",
                "dtype",
                "input_size",
                "iterations",
                "warmup",
                "checksum",
                "timing",
                "environment",
                "skip_reason",
                "memory_peak_bytes",
            ],
            "properties": {
                "schema_version": {"const": BENCHMARK_RESULT_SCHEMA_VERSION},
                "name": {"type": "string", "minLength": 1},
                "backend": {"type": "string", "minLength": 1},
                "status": {"enum": ["ok", "skipped"]},
                "dtype": {"type": "string", "minLength": 1},
                "input_size": {"type": "integer", "minimum": 0},
                "iterations": {"type": "integer", "minimum": 0},
                "warmup": {"type": "integer", "minimum": 0},
                "checksum": {"type": ["number", "null"]},
                "timing": {
                    "type": ["object", "null"],
                    "additionalProperties": False,
                    "required": ["median_seconds", "min_seconds", "max_seconds", "compile_seconds"],
                    "properties": {
                        "median_seconds": {"type": "number", "minimum": 0.0},
                        "min_seconds": {"type": "number", "minimum": 0.0},
                        "max_seconds": {"type": "number", "minimum": 0.0},
                        "compile_seconds": {"type": ["number", "null"], "minimum": 0.0},
                    },
                },
                "environment": {"type": "object"},
                "skip_reason": {"type": ["string", "null"]},
                "memory_peak_bytes": {"type": ["integer", "null"], "minimum": 0},
            },
        }
    )


def validate_benchmark_result_dict(result: dict[str, Any]) -> None:
    """Validate a benchmark result mapping.

    Args:
        result: JSON-compatible mapping to validate.

    Raises:
        ValueError: If the mapping does not satisfy the result schema support
            required by the benchmark foundation.

    Example:
        >>> timing = BenchmarkTiming(0.2, 0.1, 0.3)
        >>> result = BenchmarkResult(
        ...     name="numerical.gaussian_profile.python.small.default",
        ...     backend="python",
        ...     status="ok",
        ...     dtype="float64",
        ...     input_size=16,
        ...     iterations=1,
        ...     warmup=0,
        ...     checksum=1.0,
        ...     timing=timing,
        ... )
        >>> validate_benchmark_result_dict(result.to_dict())
    """
    if not isinstance(result, dict):
        raise ValueError(f"benchmark result must be a dictionary, got {result!r}.")
    schema = benchmark_result_schema()
    allowed = set(schema["properties"])
    missing = [key for key in schema["required"] if key not in result]
    if missing:
        raise ValueError(f"benchmark result is missing required fields: {', '.join(missing)}.")
    extra = sorted(set(result) - allowed)
    if extra:
        raise ValueError(f"benchmark result contains unknown fields: {', '.join(extra)}.")

    if result["schema_version"] != BENCHMARK_RESULT_SCHEMA_VERSION:
        raise ValueError(
            f"schema_version must be {BENCHMARK_RESULT_SCHEMA_VERSION!r}, got {result['schema_version']!r}."
        )
    _non_empty_text(result["name"], "name")
    _non_empty_text(result["backend"], "backend")
    _non_empty_text(result["dtype"], "dtype")
    status = result["status"]
    if status not in {"ok", "skipped"}:
        raise ValueError(f"status must be 'ok' or 'skipped', got {status!r}.")
    _nonnegative_int(result["input_size"], "input_size")
    _nonnegative_int(result["iterations"], "iterations")
    _nonnegative_int(result["warmup"], "warmup")
    checksum = result["checksum"]
    if checksum is not None:
        _finite_float(checksum, "checksum")
    memory_peak_bytes = result["memory_peak_bytes"]
    if memory_peak_bytes is not None:
        _nonnegative_int(memory_peak_bytes, "memory_peak_bytes")
    _json_compatible(result["environment"], "environment")

    if status == "ok":
        _validate_timing_dict(result["timing"])
        if result["skip_reason"] is not None:
            _non_empty_text(result["skip_reason"], "skip_reason")
    else:
        if result["timing"] is not None:
            raise ValueError("timing must be null for skipped benchmark results.")
        _non_empty_text(result["skip_reason"], "skip_reason")


def _validate_timing_dict(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValueError("timing is required for completed benchmark results.")
    required = {"median_seconds", "min_seconds", "max_seconds", "compile_seconds"}
    if set(value) != required:
        raise ValueError("timing must contain median_seconds, min_seconds, max_seconds, and compile_seconds.")
    timing = BenchmarkTiming(
        median_seconds=value["median_seconds"],
        min_seconds=value["min_seconds"],
        max_seconds=value["max_seconds"],
        compile_seconds=value["compile_seconds"],
    )
    timing.to_dict()


def _non_empty_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string.")


def _nonnegative_int(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer, got {value!r}.")


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
