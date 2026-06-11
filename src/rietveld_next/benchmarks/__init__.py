"""Opt-in benchmark helpers for numerical kernels."""

from rietveld_next.benchmarks.jax_gaussian import run_jax_gaussian_microbenchmark
from rietveld_next.benchmarks.optimizer import run_local_optimizer_benchmark
from rietveld_next.benchmarks.results import BenchmarkResult, BenchmarkTiming, skipped_benchmark

__all__ = [
    "BenchmarkResult",
    "BenchmarkTiming",
    "run_local_optimizer_benchmark",
    "run_jax_gaussian_microbenchmark",
    "skipped_benchmark",
]
