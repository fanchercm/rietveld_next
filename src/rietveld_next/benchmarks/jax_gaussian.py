"""Opt-in JAX Gaussian profile microbenchmark."""

from __future__ import annotations

import statistics
import time
from typing import Any

from rietveld_next.benchmarks.results import BenchmarkResult, BenchmarkTiming, skipped_benchmark


def run_jax_gaussian_microbenchmark(
    *,
    input_size: int = 256,
    iterations: int = 5,
    warmup: int = 1,
    dtype: str = "float64",
) -> BenchmarkResult:
    """Run a small JAX Gaussian profile benchmark when JAX is available.

    The first JIT call is timed separately as compile/setup time. Measured
    iterations call ``block_until_ready()`` before stopping the timer.

    Args:
        input_size: Number of axis samples. Must be positive.
        iterations: Number of measured steady-state iterations. Must be
            positive.
        warmup: Number of unmeasured warmup iterations. Must be non-negative.
        dtype: ``"float32"`` or ``"float64"``.

    Returns:
        A completed or skipped benchmark result.

    Raises:
        ValueError: If benchmark sizing inputs are invalid.
    """
    if input_size <= 0:
        raise ValueError(f"input_size must be positive, got {input_size!r}.")
    if iterations <= 0:
        raise ValueError(f"iterations must be positive, got {iterations!r}.")
    if warmup < 0:
        raise ValueError(f"warmup must be non-negative, got {warmup!r}.")
    if dtype not in {"float32", "float64"}:
        raise ValueError(f"dtype must be 'float32' or 'float64', got {dtype!r}.")

    try:
        import jax
        import jax.numpy as jnp
    except ImportError:
        return skipped_benchmark(
            name="gaussian_profile",
            backend="jax",
            dtype=dtype,
            input_size=input_size,
            reason="JAX is not installed.",
        )

    if dtype == "float64" and not bool(jax.config.read("jax_enable_x64")):
        return skipped_benchmark(
            name="gaussian_profile",
            backend="jax",
            dtype=dtype,
            input_size=input_size,
            reason="JAX float64 requested but jax_enable_x64 is disabled.",
        )

    values_dtype = jnp.float32 if dtype == "float32" else jnp.float64
    axis = jnp.linspace(-5.0, 5.0, input_size, dtype=values_dtype)

    @jax.jit
    def gaussian_sum(x: Any) -> Any:
        log_factor = 4.0 * jnp.log(jnp.asarray(2.0, dtype=values_dtype))
        normalization = jnp.sqrt(log_factor / jnp.pi)
        profile = normalization * jnp.exp(-log_factor * x**2)
        return jnp.sum(profile)

    compile_start = time.perf_counter()
    checksum_value = gaussian_sum(axis).block_until_ready()
    compile_seconds = time.perf_counter() - compile_start

    for _ in range(warmup):
        gaussian_sum(axis).block_until_ready()

    measurements: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        checksum_value = gaussian_sum(axis).block_until_ready()
        measurements.append(time.perf_counter() - start)

    device = str(checksum_value.device() if callable(getattr(checksum_value, "device", None)) else checksum_value.device)
    return BenchmarkResult(
        name="gaussian_profile",
        backend="jax",
        status="ok",
        dtype=str(axis.dtype),
        input_size=input_size,
        iterations=iterations,
        warmup=warmup,
        checksum=float(checksum_value),
        timing=BenchmarkTiming(
            median_seconds=statistics.median(measurements),
            min_seconds=min(measurements),
            max_seconds=max(measurements),
            compile_seconds=compile_seconds,
        ),
        environment={
            "device": device,
            "jax_version": jax.__version__,
        },
    )
