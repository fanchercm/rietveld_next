"""Benchmark runner CLI skeleton.

The runner keeps benchmark execution opt-in: importing this module does not run
workloads, and unavailable optional backends produce structured skipped results
instead of process failures.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import statistics
import sys
import time
from typing import Any, Sequence

from rietveld_next.benchmarks.datasets import generate_synthetic_gaussian_profile_dataset, profile_dataset_presets
from rietveld_next.benchmarks.jax_gaussian import run_jax_gaussian_microbenchmark
from rietveld_next.benchmarks.profiles import (
    run_profile_windowing_benchmark,
    run_pseudo_voigt_profile_benchmark,
    run_rust_jax_gaussian_comparison,
)
from rietveld_next.benchmarks.results import (
    BenchmarkResult,
    BenchmarkTiming,
    skipped_benchmark,
    validate_benchmark_result_dict,
)
from rietveld_next.benchmarks.taxonomy import BenchmarkIdentity, BenchmarkWorkstream
from rietveld_next.benchmarks.workflow_ai_hpc import run_sequential_refinement_workflow_overhead_benchmark


RUN_SCHEMA_VERSION = "benchmark-run-v1"
DEFAULT_KERNEL = "gaussian_profile"
NUMERICAL_KERNELS = (
    "gaussian_profile",
    "pseudo_voigt_profile",
    "profile_windowing",
    "rust_jax_gaussian_comparison",
)


class BenchmarkRunnerError(ValueError):
    """Raised when a benchmark runner selection is invalid."""


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise BenchmarkRunnerError(message)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse benchmark runner CLI arguments.

    Args:
        argv: Optional argument list. ``None`` reads from ``sys.argv``.

    Returns:
        Parsed namespace.

    Raises:
        BenchmarkRunnerError: If arguments are invalid.

    Example:
        >>> args = parse_args(["--family", "numerical", "--backend", "rust"])
        >>> args.backend
        'rust'
    """
    parser = _ArgumentParser(prog="rietveld-next-benchmark", description="Run opt-in benchmark smoke workloads.")
    parser.add_argument(
        "--family",
        choices=[workstream.value for workstream in BenchmarkWorkstream],
        default=BenchmarkWorkstream.NUMERICAL.value,
        help="Benchmark family/workstream to select.",
    )
    parser.add_argument("--backend", choices=["python", "jax", "rust"], default="python", help="Backend to select.")
    parser.add_argument("--kernel", choices=NUMERICAL_KERNELS, default=DEFAULT_KERNEL, help="Numerical kernel to select.")
    parser.add_argument("--size", choices=sorted(profile_dataset_presets()), default="small", help="Dataset size preset.")
    parser.add_argument("--iterations", type=_positive_int_arg, default=1, help="Measured steady-state iterations.")
    parser.add_argument("--warmup", type=_nonnegative_int_arg, default=0, help="Unmeasured warmup iterations.")
    parser.add_argument("--dtype", choices=["float32", "float64"], default="float64", help="Numeric dtype request.")
    parser.add_argument("--seed", type=_nonnegative_int_arg, default=0, help="Synthetic dataset seed.")
    parser.add_argument("--variant", type=_slug_arg, default="synthetic", help="Benchmark variant slug.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON output path.")
    parser.add_argument("--markdown-output", type=Path, default=None, help="Optional Markdown summary output path.")
    return parser.parse_args(argv)


def run_selected_benchmark(args: argparse.Namespace) -> dict[str, Any]:
    """Run the selected benchmark skeleton and return JSON-compatible output.

    Args:
        args: Parsed CLI namespace from :func:`parse_args`.

    Returns:
        Benchmark run envelope containing selection metadata and one result.
    """
    kernel = "sequential_refinement" if args.family == BenchmarkWorkstream.WORKFLOW.value else args.kernel
    identity_backend = "rust_jax" if args.kernel == "rust_jax_gaussian_comparison" else args.backend
    identity = BenchmarkIdentity(
        workstream=args.family,
        kernel=kernel,
        backend=identity_backend,
        size=args.size,
        variant=args.variant,
    )
    presets = profile_dataset_presets()
    input_size = _workflow_sequence_points(args.size) if args.family == BenchmarkWorkstream.WORKFLOW.value else presets[args.size].sample_count

    if args.family == BenchmarkWorkstream.WORKFLOW.value:
        if args.backend != "python":
            result = skipped_benchmark(
                name=identity.benchmark_id(),
                backend=args.backend,
                dtype=args.dtype,
                input_size=input_size,
                iterations=args.iterations,
                warmup=args.warmup,
                reason="Workflow smoke benchmarks currently run only on the Python backend.",
                environment=_base_environment(args.seed, identity),
            )
        elif args.dtype != "float64":
            result = skipped_benchmark(
                name=identity.benchmark_id(),
                backend=args.backend,
                dtype=args.dtype,
                input_size=input_size,
                iterations=args.iterations,
                warmup=args.warmup,
                reason="Workflow smoke benchmark uses Python float data; only dtype='float64' is reported.",
                environment=_base_environment(args.seed, identity),
            )
        else:
            raw_result = run_sequential_refinement_workflow_overhead_benchmark(
                sequence_points=input_size,
                iterations=args.iterations,
                warmup=args.warmup,
                seed=args.seed,
            )
            result = _normalize_result(
                raw_result,
                identity=identity,
                seed=args.seed,
                requested_iterations=args.iterations,
                requested_warmup=args.warmup,
            )
    elif args.family != BenchmarkWorkstream.NUMERICAL.value:
        result = skipped_benchmark(
            name=identity.benchmark_id(),
            backend=args.backend,
            dtype=args.dtype,
            input_size=input_size,
            iterations=args.iterations,
            warmup=args.warmup,
            reason=f"Benchmark family {args.family!r} is registered in the taxonomy but has no runner skeleton yet.",
            environment=_base_environment(args.seed, identity),
        )
    elif args.kernel == "rust_jax_gaussian_comparison":
        result = _normalize_result(
            run_rust_jax_gaussian_comparison(input_size=input_size, dtype=args.dtype),
            identity=identity,
            seed=args.seed,
            requested_iterations=args.iterations,
            requested_warmup=args.warmup,
        )
    elif args.kernel == "pseudo_voigt_profile":
        if args.backend != "python":
            result = skipped_benchmark(
                name=identity.benchmark_id(),
                backend=args.backend,
                dtype=args.dtype,
                input_size=input_size,
                iterations=args.iterations,
                warmup=args.warmup,
                reason="Pseudo-Voigt profile smoke benchmark currently runs only on the Python backend.",
                environment=_base_environment(args.seed, identity),
            )
        elif args.dtype != "float64":
            result = skipped_benchmark(
                name=identity.benchmark_id(),
                backend=args.backend,
                dtype=args.dtype,
                input_size=input_size,
                iterations=args.iterations,
                warmup=args.warmup,
                reason="Pseudo-Voigt profile smoke benchmark uses Python float data; only dtype='float64' is reported.",
                environment=_base_environment(args.seed, identity),
            )
        else:
            raw_result = run_pseudo_voigt_profile_benchmark(
                size=args.size,
                iterations=args.iterations,
                warmup=args.warmup,
                seed=args.seed,
            )
            result = _normalize_result(
                raw_result,
                identity=identity,
                seed=args.seed,
                requested_iterations=args.iterations,
                requested_warmup=args.warmup,
            )
    elif args.kernel == "profile_windowing":
        if args.backend != "python":
            result = skipped_benchmark(
                name=identity.benchmark_id(),
                backend=args.backend,
                dtype=args.dtype,
                input_size=input_size,
                iterations=args.iterations,
                warmup=args.warmup,
                reason="Profile windowing smoke benchmark currently runs only on the Python backend.",
                environment=_base_environment(args.seed, identity),
            )
        elif args.dtype != "float64":
            result = skipped_benchmark(
                name=identity.benchmark_id(),
                backend=args.backend,
                dtype=args.dtype,
                input_size=input_size,
                iterations=args.iterations,
                warmup=args.warmup,
                reason="Profile windowing smoke benchmark uses Python float data; only dtype='float64' is reported.",
                environment=_base_environment(args.seed, identity),
            )
        else:
            raw_result = run_profile_windowing_benchmark(
                size=args.size,
                iterations=args.iterations,
                warmup=args.warmup,
                seed=args.seed,
            )
            result = _normalize_result(
                raw_result,
                identity=identity,
                seed=args.seed,
                requested_iterations=args.iterations,
                requested_warmup=args.warmup,
            )
    elif args.backend == "python":
        if args.dtype != "float64":
            result = skipped_benchmark(
                name=identity.benchmark_id(),
                backend=args.backend,
                dtype=args.dtype,
                input_size=input_size,
                iterations=args.iterations,
                warmup=args.warmup,
                reason="Python smoke benchmark uses Python float data; only dtype='float64' is reported.",
                environment=_base_environment(args.seed, identity),
            )
        else:
            result = _run_python_synthetic_profile_smoke(args, identity)
    elif args.backend == "jax":
        raw_result = run_jax_gaussian_microbenchmark(
            input_size=input_size,
            iterations=args.iterations,
            warmup=args.warmup,
            dtype=args.dtype,
        )
        result = _normalize_result(raw_result, identity=identity, seed=args.seed, requested_iterations=args.iterations, requested_warmup=args.warmup)
    else:
        result = skipped_benchmark(
            name=identity.benchmark_id(),
            backend=args.backend,
            dtype=args.dtype,
            input_size=input_size,
            iterations=args.iterations,
            warmup=args.warmup,
            reason="Rust benchmark backend is optional and is not registered in this Python runner skeleton.",
            environment=_base_environment(args.seed, identity),
        )

    result_dict = result.to_dict()
    validate_benchmark_result_dict(result_dict)
    return {
        "schema_version": RUN_SCHEMA_VERSION,
        "selection": {
            "family": args.family,
            "backend": args.backend,
            "kernel": args.kernel,
            "size": args.size,
            "iterations": args.iterations,
            "warmup": args.warmup,
            "dtype": args.dtype,
            "seed": args.seed,
            "variant": args.variant,
        },
        "results": [result_dict],
    }


def write_json_output(output: dict[str, Any], path: Path) -> None:
    """Write a benchmark run envelope as deterministic JSON.

    Args:
        output: JSON-compatible run envelope.
        path: Destination path. Parent directories are created if needed.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown_summary(output: dict[str, Any], path: Path) -> None:
    """Write a compact Markdown benchmark summary.

    Args:
        output: JSON-compatible run envelope.
        path: Destination path. Parent directories are created if needed.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Benchmark Summary", "", "| Benchmark | Backend | Status | Median (s) | Reason |", "| --- | --- | --- | ---: | --- |"]
    for result in output["results"]:
        timing = result["timing"]
        median = "" if timing is None else f"{timing['median_seconds']:.9g}"
        reason = "" if result["skip_reason"] is None else str(result["skip_reason"])
        lines.append(f"| {result['name']} | {result['backend']} | {result['status']} | {median} | {reason} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the benchmark CLI skeleton.

    Args:
        argv: Optional command-line arguments.

    Returns:
        Process exit code. Invalid arguments return ``2``; skipped optional
        backends still return ``0`` with a skipped result.
    """
    try:
        args = parse_args(argv)
        output = run_selected_benchmark(args)
    except (BenchmarkRunnerError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.output is None:
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        write_json_output(output, args.output)
    if args.markdown_output is not None:
        write_markdown_summary(output, args.markdown_output)
    return 0


def _run_python_synthetic_profile_smoke(args: argparse.Namespace, identity: BenchmarkIdentity) -> BenchmarkResult:
    for _ in range(args.warmup):
        generate_synthetic_gaussian_profile_dataset(size=args.size, seed=args.seed, variant=args.variant)

    measurements: list[float] = []
    checksum = 0.0
    for _ in range(args.iterations):
        start = time.perf_counter()
        dataset = generate_synthetic_gaussian_profile_dataset(size=args.size, seed=args.seed, variant=args.variant)
        checksum = dataset.checksum()
        measurements.append(time.perf_counter() - start)

    environment = _base_environment(args.seed, identity)
    environment["dataset"] = dataset.metadata
    return BenchmarkResult(
        name=identity.benchmark_id(),
        backend="python",
        status="ok",
        dtype=args.dtype,
        input_size=len(dataset.x_degrees),
        iterations=args.iterations,
        warmup=args.warmup,
        checksum=checksum,
        timing=BenchmarkTiming(
            median_seconds=statistics.median(measurements),
            min_seconds=min(measurements),
            max_seconds=max(measurements),
            compile_seconds=None,
        ),
        environment=environment,
    )


def _normalize_result(
    result: BenchmarkResult,
    *,
    identity: BenchmarkIdentity,
    seed: int,
    requested_iterations: int,
    requested_warmup: int,
) -> BenchmarkResult:
    environment = dict(result.environment)
    environment.update(_base_environment(seed, identity))
    return BenchmarkResult(
        name=identity.benchmark_id(),
        backend=result.backend,
        status=result.status,
        dtype=result.dtype,
        input_size=result.input_size,
        iterations=result.iterations if result.status == "ok" else requested_iterations,
        warmup=result.warmup if result.status == "ok" else requested_warmup,
        checksum=result.checksum,
        timing=result.timing,
        environment=environment,
        skip_reason=result.skip_reason,
        memory_peak_bytes=result.memory_peak_bytes,
    )


def _workflow_sequence_points(size: str) -> int:
    mapping = {
        "small": 4,
        "medium": 16,
        "large": 64,
    }
    return mapping[size]


def _base_environment(seed: int, identity: BenchmarkIdentity) -> dict[str, Any]:
    return {
        "benchmark_id": identity.benchmark_id(),
        "benchmark_identity": identity.to_dict(),
        "python_version": platform.python_version(),
        "platform_machine": platform.machine(),
        "platform_system": platform.system(),
        "seed": seed,
        "timing_model": {
            "compile_seconds": "one-time compile or setup time when the backend exposes it",
            "warmup": "unmeasured iterations before steady-state timing",
            "steady_state": "measured iterations summarized by median/min/max wall time",
        },
    }


def _positive_int_arg(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def _nonnegative_int_arg(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def _slug_arg(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not value.replace("_", "a").isalnum()
        or not value[0].isalpha()
        or value.lower() != value
    ):
        raise argparse.ArgumentTypeError("must be a lowercase slug using letters, digits, or underscores")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
