"""Opt-in profile kernel benchmarks and comparison helpers."""

from __future__ import annotations

from dataclasses import dataclass
import math
import platform
import statistics
import time
from collections.abc import Sequence
from typing import Any

from rietveld_next.benchmarks.datasets import (
    GaussianPeak,
    SyntheticProfileDataset,
    generate_synthetic_gaussian_profile_dataset,
)
from rietveld_next.benchmarks.results import BenchmarkResult, BenchmarkTiming, skipped_benchmark
from rietveld_next.diffraction.profiles import gaussian_profile, peak_window_indices, pseudo_voigt_profile


GAUSSIAN_FLOAT64_ABS_TOLERANCE = 1.0e-12
GAUSSIAN_FLOAT64_REL_TOLERANCE = 1.0e-12
GAUSSIAN_FLOAT32_ABS_TOLERANCE = 5.0e-5
GAUSSIAN_FLOAT32_REL_TOLERANCE = 5.0e-5
WINDOW_ABS_TOLERANCE = 1.0e-10


@dataclass(frozen=True)
class GaussianComparisonReport:
    """Cross-backend Gaussian comparison diagnostics.

    Args:
        dtype: Numeric dtype used by the JAX-side comparison.
        value_count: Number of profile samples compared.
        max_abs_error: Maximum absolute sample-wise error.
        max_rel_error: Maximum relative sample-wise error.
        checksum_abs_error: Absolute error between output checksums.
        abs_tolerance: Absolute tolerance applied to sample values.
        rel_tolerance: Relative tolerance applied to sample values.

    Example:
        >>> report = compare_gaussian_profile_outputs([1.0], [1.0], dtype="float64")
        >>> report.max_abs_error
        0.0
    """

    dtype: str
    value_count: int
    max_abs_error: float
    max_rel_error: float
    checksum_abs_error: float
    abs_tolerance: float
    rel_tolerance: float

    def to_dict(self) -> dict[str, float | int | str]:
        """Return a deterministic JSON-compatible report mapping."""
        return {
            "dtype": self.dtype,
            "value_count": self.value_count,
            "max_abs_error": self.max_abs_error,
            "max_rel_error": self.max_rel_error,
            "checksum_abs_error": self.checksum_abs_error,
            "abs_tolerance": self.abs_tolerance,
            "rel_tolerance": self.rel_tolerance,
        }


class GaussianComparisonMismatch(AssertionError):
    """Raised when Rust-style and JAX Gaussian outputs exceed tolerance."""


def compare_gaussian_profile_outputs(
    rust_values: Sequence[float],
    jax_values: Sequence[float],
    *,
    dtype: str,
) -> GaussianComparisonReport:
    """Compare Rust-style and JAX Gaussian profile outputs.

    Args:
        rust_values: Profile values produced by the Rust backend or a
            Rust-compatible fixture.
        jax_values: Profile values produced by the JAX backend.
        dtype: ``"float64"`` applies strict tolerance; ``"float32"`` applies
            an explicitly relaxed tolerance.

    Returns:
        Comparison diagnostics including value and checksum errors.

    Raises:
        GaussianComparisonMismatch: If sample-wise errors exceed tolerance.
        ValueError: If shapes, dtype, or values are invalid.
    """
    rust_profile = _finite_profile_values(rust_values, "rust_values")
    jax_profile = _finite_profile_values(jax_values, "jax_values")
    if len(rust_profile) != len(jax_profile):
        raise ValueError(
            f"rust_values and jax_values must have the same length, got {len(rust_profile)} and {len(jax_profile)}."
        )
    abs_tolerance, rel_tolerance = _gaussian_tolerance(dtype)

    max_abs_error = 0.0
    max_rel_error = 0.0
    for rust_value, jax_value in zip(rust_profile, jax_profile, strict=True):
        abs_error = abs(rust_value - jax_value)
        rel_error = abs_error / max(abs(rust_value), abs(jax_value), 1.0e-300)
        max_abs_error = max(max_abs_error, abs_error)
        max_rel_error = max(max_rel_error, rel_error)

    checksum_abs_error = abs(sum(rust_profile) - sum(jax_profile))
    report = GaussianComparisonReport(
        dtype=dtype,
        value_count=len(rust_profile),
        max_abs_error=max_abs_error,
        max_rel_error=max_rel_error,
        checksum_abs_error=checksum_abs_error,
        abs_tolerance=abs_tolerance,
        rel_tolerance=rel_tolerance,
    )
    if max_abs_error > abs_tolerance and max_rel_error > rel_tolerance:
        raise GaussianComparisonMismatch(
            "Rust/JAX Gaussian profile mismatch: "
            f"max_abs_error={max_abs_error:.17g} exceeds abs_tolerance={abs_tolerance:.17g}; "
            f"max_rel_error={max_rel_error:.17g} exceeds rel_tolerance={rel_tolerance:.17g}; "
            f"checksum_abs_error={checksum_abs_error:.17g}."
        )
    return report


def run_rust_jax_gaussian_comparison(
    *,
    rust_values: Sequence[float] | None = None,
    input_size: int = 128,
    dtype: str = "float64",
) -> BenchmarkResult:
    """Compare optional Rust Gaussian output with JAX output when available.

    Args:
        rust_values: Rust backend profile samples in the same order as the
            deterministic comparison axis. ``None`` returns a skipped result
            because this repository snapshot has no compiled Rust profile
            runner.
        input_size: Number of comparison axis samples. Must be positive.
        dtype: ``"float32"`` or ``"float64"``.

    Returns:
        Completed comparison benchmark or a structured skipped result.

    Raises:
        GaussianComparisonMismatch: If both outputs are available but exceed
            tolerance.
        ValueError: If inputs are invalid.
    """
    _positive_int(input_size, "input_size")
    _gaussian_tolerance(dtype)
    if rust_values is None:
        return skipped_benchmark(
            name="rust_jax_gaussian_profile_comparison",
            backend="rust_jax",
            dtype=dtype,
            input_size=input_size,
            reason="Rust Gaussian profile output was not supplied; no compiled Rust benchmark runner exists in this snapshot.",
            environment=_profile_environment(seed=0, issue_numbers=[294]),
        )

    try:
        import jax
        import jax.numpy as jnp
    except ImportError:
        return skipped_benchmark(
            name="rust_jax_gaussian_profile_comparison",
            backend="rust_jax",
            dtype=dtype,
            input_size=input_size,
            reason="JAX is not installed.",
            environment=_profile_environment(seed=0, issue_numbers=[294]),
        )

    if dtype == "float64" and not bool(jax.config.read("jax_enable_x64")):
        return skipped_benchmark(
            name="rust_jax_gaussian_profile_comparison",
            backend="rust_jax",
            dtype=dtype,
            input_size=input_size,
            reason="JAX float64 requested but jax_enable_x64 is disabled.",
            environment=_profile_environment(seed=0, issue_numbers=[294]),
        )

    values_dtype = jnp.float32 if dtype == "float32" else jnp.float64
    axis = jnp.linspace(-5.0, 5.0, input_size, dtype=values_dtype)

    def profile(values: Any) -> Any:
        log_factor = 4.0 * jnp.log(jnp.asarray(2.0, dtype=values_dtype))
        scale = jnp.sqrt(log_factor / jnp.pi)
        return scale * jnp.exp(-log_factor * values**2)

    start = time.perf_counter()
    jax_profile = profile(axis).block_until_ready()
    report = compare_gaussian_profile_outputs(rust_values, [float(value) for value in jax_profile.tolist()], dtype=dtype)
    elapsed = time.perf_counter() - start
    environment = _profile_environment(seed=0, issue_numbers=[294])
    environment.update(
        {
            "comparison": report.to_dict(),
            "tolerance_policy": _tolerance_policy(dtype),
            "jax_version": jax.__version__,
            "device": str(jax_profile.device() if callable(getattr(jax_profile, "device", None)) else jax_profile.device),
        }
    )
    return BenchmarkResult(
        name="rust_jax_gaussian_profile_comparison",
        backend="rust_jax",
        status="ok",
        dtype=str(jax_profile.dtype),
        input_size=input_size,
        iterations=1,
        warmup=0,
        checksum=sum(float(value) for value in jax_profile.tolist()),
        timing=BenchmarkTiming(elapsed, elapsed, elapsed),
        environment=environment,
    )


def run_pseudo_voigt_profile_benchmark(
    *,
    size: str = "small",
    iterations: int = 1,
    warmup: int = 0,
    seed: int = 0,
    eta: float = 0.35,
) -> BenchmarkResult:
    """Run a deterministic pseudo-Voigt profile microbenchmark.

    Args:
        size: Synthetic dataset preset. Supports at least ``"small"`` and
            ``"medium"``; ``"large"`` remains opt-in through explicit calls.
        iterations: Number of measured iterations. Must be positive.
        warmup: Number of unmeasured warmup iterations. Must be non-negative.
        seed: Synthetic dataset seed recorded in metadata.
        eta: Lorentzian mixing fraction on ``[0, 1]``.

    Returns:
        Benchmark result with checksum, pair counts, and timing statistics.
    """
    _positive_int(iterations, "iterations")
    _nonnegative_int(warmup, "warmup")
    _nonnegative_int(seed, "seed")
    _unit_interval(eta, "eta")
    dataset = generate_synthetic_gaussian_profile_dataset(size=size, seed=seed, variant="pseudo_voigt")

    for _ in range(warmup):
        _dense_pseudo_voigt_profile(dataset, eta=eta)

    measurements: list[float] = []
    checksum = 0.0
    for _ in range(iterations):
        start = time.perf_counter()
        profile_values = _dense_pseudo_voigt_profile(dataset, eta=eta)
        checksum = sum(profile_values)
        measurements.append(time.perf_counter() - start)

    environment = _profile_environment(seed=seed, issue_numbers=[298])
    environment.update(
        {
            "dataset": dataset.metadata,
            "eta": eta,
            "peak_count": len(dataset.peaks),
            "evaluated_point_peak_pairs": len(dataset.x_degrees) * len(dataset.peaks),
            "profile_model": "area_scaled_pseudo_voigt",
            "assumptions": [
                "synthetic Gaussian dataset peak amplitudes are used as area proxies for benchmark workload generation",
                "this benchmark measures Python reference-kernel overhead and is not a scientific validation result",
            ],
        }
    )
    return BenchmarkResult(
        name="pseudo_voigt_profile",
        backend="python",
        status="ok",
        dtype="float64",
        input_size=len(dataset.x_degrees),
        iterations=iterations,
        warmup=warmup,
        checksum=checksum,
        timing=BenchmarkTiming(
            median_seconds=statistics.median(measurements),
            min_seconds=min(measurements),
            max_seconds=max(measurements),
        ),
        environment=environment,
    )


def run_profile_windowing_benchmark(
    *,
    size: str = "small",
    iterations: int = 1,
    warmup: int = 0,
    seed: int = 0,
    width_factor: float = 12.0,
) -> BenchmarkResult:
    """Benchmark dense Gaussian profile evaluation against finite windows.

    Args:
        size: Synthetic dataset preset.
        iterations: Number of measured iterations. Must be positive.
        warmup: Number of unmeasured warmup iterations. Must be non-negative.
        seed: Synthetic dataset seed recorded in metadata.
        width_factor: Positive FWHM multiplier for each peak half-window.

    Returns:
        Benchmark result with pair-count, memory, and dense/window agreement
        diagnostics.
    """
    _positive_int(iterations, "iterations")
    _nonnegative_int(warmup, "warmup")
    _nonnegative_int(seed, "seed")
    width_factor_value = _positive_float(width_factor, "width_factor")
    dataset = generate_synthetic_gaussian_profile_dataset(size=size, seed=seed, variant="windowed_gaussian")

    dense_reference = _dense_gaussian_profile(dataset)
    for _ in range(warmup):
        _windowed_gaussian_profile(dataset, width_factor=width_factor_value)

    measurements: list[float] = []
    checksum = 0.0
    windowed_values: list[float] = []
    evaluated_pairs = 0
    for _ in range(iterations):
        start = time.perf_counter()
        windowed_values, evaluated_pairs = _windowed_gaussian_profile(dataset, width_factor=width_factor_value)
        checksum = sum(windowed_values)
        measurements.append(time.perf_counter() - start)

    dense_pairs = len(dataset.x_degrees) * len(dataset.peaks)
    max_abs_error, max_rel_error = _profile_errors(dense_reference, windowed_values)
    if max_abs_error > WINDOW_ABS_TOLERANCE:
        raise GaussianComparisonMismatch(
            "Windowed Gaussian profile exceeded truncation tolerance: "
            f"max_abs_error={max_abs_error:.17g} exceeds abs_tolerance={WINDOW_ABS_TOLERANCE:.17g}; "
            f"max_rel_error={max_rel_error:.17g}; width_factor={width_factor_value:.17g}."
        )

    environment = _profile_environment(seed=seed, issue_numbers=[299])
    environment.update(
        {
            "dataset": dataset.metadata,
            "width_factor": width_factor_value,
            "dense_point_peak_pairs": dense_pairs,
            "windowed_point_peak_pairs": evaluated_pairs,
            "point_peak_pair_reduction_fraction": 1.0 - evaluated_pairs / float(dense_pairs),
            "dense_pair_memory_bytes": dense_pairs * 8,
            "windowed_pair_memory_bytes": evaluated_pairs * 8,
            "max_abs_error": max_abs_error,
            "max_rel_error": max_rel_error,
            "abs_tolerance": WINDOW_ABS_TOLERANCE,
            "profile_model": "area_scaled_gaussian",
            "assumptions": [
                "finite windows are compared against the dense Gaussian reference with an explicit absolute truncation tolerance",
                "pair memory estimates assume one float64 contribution per evaluated point-peak pair",
            ],
        }
    )
    return BenchmarkResult(
        name="profile_windowing",
        backend="python",
        status="ok",
        dtype="float64",
        input_size=len(dataset.x_degrees),
        iterations=iterations,
        warmup=warmup,
        checksum=checksum,
        timing=BenchmarkTiming(
            median_seconds=statistics.median(measurements),
            min_seconds=min(measurements),
            max_seconds=max(measurements),
        ),
        environment=environment,
    )


def _dense_pseudo_voigt_profile(dataset: SyntheticProfileDataset, *, eta: float) -> list[float]:
    total = [0.0 for _ in dataset.x_degrees]
    for peak in dataset.peaks:
        values = pseudo_voigt_profile(
            dataset.x_degrees,
            center=peak.position_degrees,
            fwhm=peak.fwhm_degrees,
            eta=eta,
            area=peak.amplitude_counts,
        )
        total = [left + right for left, right in zip(total, values, strict=True)]
    return total


def _dense_gaussian_profile(dataset: SyntheticProfileDataset) -> list[float]:
    total = [0.0 for _ in dataset.x_degrees]
    for peak in dataset.peaks:
        values = _gaussian_peak_values(dataset.x_degrees, peak)
        total = [left + right for left, right in zip(total, values, strict=True)]
    return total


def _windowed_gaussian_profile(dataset: SyntheticProfileDataset, *, width_factor: float) -> tuple[list[float], int]:
    total = [0.0 for _ in dataset.x_degrees]
    evaluated_pairs = 0
    for peak in dataset.peaks:
        start, stop = peak_window_indices(
            dataset.x_degrees,
            center=peak.position_degrees,
            fwhm=peak.fwhm_degrees,
            width_factor=width_factor,
        )
        window_axis = dataset.x_degrees[start:stop]
        values = _gaussian_peak_values(window_axis, peak)
        evaluated_pairs += len(window_axis)
        for offset, value in enumerate(values, start=start):
            total[offset] += value
    return total, evaluated_pairs


def _gaussian_peak_values(axis: Sequence[float], peak: GaussianPeak) -> list[float]:
    return gaussian_profile(
        axis,
        center=peak.position_degrees,
        fwhm=peak.fwhm_degrees,
        area=peak.amplitude_counts,
    )


def _profile_errors(reference: Sequence[float], actual: Sequence[float]) -> tuple[float, float]:
    if len(reference) != len(actual):
        raise ValueError(f"profile lengths must match, got {len(reference)} and {len(actual)}.")
    max_abs_error = 0.0
    max_rel_error = 0.0
    for reference_value, actual_value in zip(reference, actual, strict=True):
        abs_error = abs(reference_value - actual_value)
        rel_error = abs_error / max(abs(reference_value), abs(actual_value), 1.0e-300)
        max_abs_error = max(max_abs_error, abs_error)
        max_rel_error = max(max_rel_error, rel_error)
    return max_abs_error, max_rel_error


def _profile_environment(*, seed: int, issue_numbers: list[int]) -> dict[str, Any]:
    return {
        "python_version": platform.python_version(),
        "platform_machine": platform.machine(),
        "platform_system": platform.system(),
        "seed": seed,
        "issue_numbers": issue_numbers,
    }


def _tolerance_policy(dtype: str) -> dict[str, float | str]:
    abs_tolerance, rel_tolerance = _gaussian_tolerance(dtype)
    precision = "relaxed_float32" if dtype == "float32" else "strict_float64"
    return {
        "precision": precision,
        "abs_tolerance": abs_tolerance,
        "rel_tolerance": rel_tolerance,
    }


def _gaussian_tolerance(dtype: str) -> tuple[float, float]:
    if dtype == "float64":
        return GAUSSIAN_FLOAT64_ABS_TOLERANCE, GAUSSIAN_FLOAT64_REL_TOLERANCE
    if dtype == "float32":
        return GAUSSIAN_FLOAT32_ABS_TOLERANCE, GAUSSIAN_FLOAT32_REL_TOLERANCE
    raise ValueError(f"dtype must be 'float32' or 'float64', got {dtype!r}.")


def _finite_profile_values(values: Sequence[float], name: str) -> list[float]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    parsed: list[float] = []
    for index, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
            raise ValueError(f"{name}[{index}] must be a finite number, got {value!r}.")
        parsed.append(float(value))
    return parsed


def _positive_int(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value!r}.")


def _nonnegative_int(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer, got {value!r}.")


def _positive_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be a positive finite number, got {value!r}.")
    return float(value)


def _unit_interval(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be a finite number between 0 and 1, got {value!r}.")
    return float(value)
