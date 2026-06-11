"""Opt-in synthetic local optimizer benchmark."""

from __future__ import annotations

import platform
import time

from rietveld_next.benchmarks.results import BenchmarkResult, BenchmarkTiming
from rietveld_next.optimization.diagnostics import parameter_error_metrics
from rietveld_next.optimization.local import LocalOptimizerOptions, coordinate_search_minimize
from rietveld_next.optimization.objectives import least_squares_evaluation
from rietveld_next.optimization.transforms import BoundTransform


def run_local_optimizer_benchmark(*, dimensions: int = 2) -> BenchmarkResult:
    """Run a small deterministic local optimizer benchmark.

    Args:
        dimensions: Number of independent quadratic parameters. Must be
            positive.

    Returns:
        Machine-readable benchmark result with convergence metrics in the
        environment metadata.
    """
    if isinstance(dimensions, bool) or not isinstance(dimensions, int) or dimensions <= 0:
        raise ValueError(f"dimensions must be a positive integer, got {dimensions!r}.")

    target = tuple(float(index + 1) for index in range(dimensions))
    initial = tuple(0.0 for _ in range(dimensions))
    upper_bound = max(10.0, float(dimensions) + 1.0)
    bounds = tuple(BoundTransform(lower=-10.0, upper=upper_bound) for _ in range(dimensions))

    def objective(parameters: tuple[float, ...]):
        return least_squares_evaluation(parameters, [value - expected for value, expected in zip(parameters, target, strict=True)])

    start = time.perf_counter()
    report = coordinate_search_minimize(
        objective,
        initial,
        bounds=bounds,
        options=LocalOptimizerOptions(max_iterations=200, initial_step=1.0, tolerance=1.0e-6),
    )
    elapsed = time.perf_counter() - start
    errors = parameter_error_metrics(report.parameters, target)

    return BenchmarkResult(
        name="local_optimizer_quadratic",
        backend="python",
        status="ok",
        dtype="float64",
        input_size=dimensions,
        iterations=1,
        warmup=0,
        checksum=sum(report.parameters) + report.objective_value,
        timing=BenchmarkTiming(
            median_seconds=elapsed,
            min_seconds=elapsed,
            max_seconds=elapsed,
            compile_seconds=None,
        ),
        environment={
            "converged": report.converged,
            "status": report.status,
            "optimizer_iterations": report.iterations,
            "function_evaluations": report.evaluations,
            "final_objective": report.objective_value,
            "max_abs_parameter_error": errors["max_abs_error"],
            "rms_parameter_error": errors["rms_error"],
            "python_version": platform.python_version(),
        },
    )
