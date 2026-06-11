"""Opt-in benchmark helpers for numerical kernels."""

from rietveld_next.benchmarks.datasets import (
    GaussianPeak,
    ProfileDatasetPreset,
    SyntheticProfileDataset,
    generate_synthetic_gaussian_profile_dataset,
    profile_dataset_presets,
)
from rietveld_next.benchmarks.jax_gaussian import run_jax_gaussian_microbenchmark
from rietveld_next.benchmarks.optimizer import run_local_optimizer_benchmark
from rietveld_next.benchmarks.results import (
    BENCHMARK_RESULT_SCHEMA_VERSION,
    BenchmarkResult,
    BenchmarkTiming,
    benchmark_result_schema,
    skipped_benchmark,
    validate_benchmark_result_dict,
)
from rietveld_next.benchmarks.taxonomy import (
    BenchmarkFamily,
    BenchmarkIdentity,
    BenchmarkKind,
    BenchmarkWorkstream,
    benchmark_families,
    build_benchmark_id,
    parse_benchmark_id,
)

__all__ = [
    "BENCHMARK_RESULT_SCHEMA_VERSION",
    "BenchmarkFamily",
    "BenchmarkIdentity",
    "BenchmarkKind",
    "BenchmarkResult",
    "BenchmarkTiming",
    "BenchmarkWorkstream",
    "GaussianPeak",
    "ProfileDatasetPreset",
    "SyntheticProfileDataset",
    "benchmark_families",
    "benchmark_result_schema",
    "build_benchmark_id",
    "generate_synthetic_gaussian_profile_dataset",
    "parse_benchmark_id",
    "profile_dataset_presets",
    "run_jax_gaussian_microbenchmark",
    "run_local_optimizer_benchmark",
    "skipped_benchmark",
    "validate_benchmark_result_dict",
]
