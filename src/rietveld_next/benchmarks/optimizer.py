"""Opt-in synthetic local optimizer benchmark."""

from __future__ import annotations

import platform
import time

from rietveld_next.benchmarks.results import BenchmarkResult, BenchmarkTiming, skipped_benchmark
from rietveld_next.optimization.global_search import MultiStartOptions, multi_start_minimize
from rietveld_next.optimization.jacobian import SparseJacobian, finite_difference_jacobian
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
    failure_report = coordinate_search_minimize(lambda parameters: (_ for _ in ()).throw(ValueError("synthetic invalid model")), initial)
    unbounded_report = coordinate_search_minimize(
        objective,
        initial,
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
            "case_modes": ["bounded_coordinate_search", "unbounded_lm_compatible_quadratic", "invalid_initial_model"],
            "failure_status": failure_report.status,
            "unbounded_status": unbounded_report.status,
            "unbounded_converged": unbounded_report.converged,
            "max_abs_parameter_error": errors["max_abs_error"],
            "rms_parameter_error": errors["rms_error"],
            "python_version": platform.python_version(),
        },
    )


def run_sparse_jacobian_assembly_benchmark(*, dimensions: int = 4) -> BenchmarkResult:
    """Run a deterministic sparse Jacobian assembly smoke benchmark.

    Args:
        dimensions: Number of parameters and residuals in a diagonal synthetic
            fixture. Must be positive.

    Returns:
        Benchmark result containing non-zero count and checksum metadata.
    """
    _positive_int(dimensions, "dimensions")
    dense = [
        [float(row + 1) if row == column else 0.0 for column in range(dimensions)]
        for row in range(dimensions)
    ]

    start = time.perf_counter()
    jacobian = SparseJacobian.from_dense(
        dense,
        parameter_labels=[f"p{index}" for index in range(dimensions)],
        parameter_units=["dimensionless" for _ in range(dimensions)],
    )
    elapsed = time.perf_counter() - start
    checksum = sum(entry.value for entry in jacobian.entries)
    dense_round_trip = jacobian.to_dense()
    reference_matches = dense_round_trip == dense
    entry_count = dimensions * dimensions

    return BenchmarkResult(
        name="sparse_jacobian_assembly",
        backend="python",
        status="ok",
        dtype="float64",
        input_size=dimensions,
        iterations=1,
        warmup=0,
        checksum=checksum,
        timing=BenchmarkTiming(elapsed, elapsed, elapsed),
        environment={
            "nonzero_count": len(jacobian.entries),
            "density": len(jacobian.entries) / float(entry_count),
            "reference_matches_dense_fixture": reference_matches,
            "reference_max_abs_error": _max_matrix_abs_error(dense_round_trip, dense),
            "row_count": jacobian.row_count,
            "column_count": jacobian.column_count,
            "python_version": platform.python_version(),
        },
    )


def run_automatic_differentiation_benchmark(*, dimensions: int = 2) -> BenchmarkResult:
    """Run a deterministic JAX automatic-differentiation benchmark when available.

    Args:
        dimensions: Number of parameters and residuals in the quadratic fixture.

    Returns:
        Benchmark result, or a structured skipped result when JAX is unavailable
        or float64 is disabled.
    """
    _positive_int(dimensions, "dimensions")
    try:
        import jax
        import jax.numpy as jnp
    except ImportError:
        return skipped_benchmark(
            name="jax_autodiff_jacobian",
            backend="jax",
            dtype="float64",
            input_size=dimensions,
            reason="JAX is not installed.",
            iterations=0,
            warmup=0,
            environment={"derivative_backend": "jax_jacfwd"},
        )

    if not bool(jax.config.read("jax_enable_x64")):
        return skipped_benchmark(
            name="jax_autodiff_jacobian",
            backend="jax",
            dtype="float64",
            input_size=dimensions,
            reason="JAX float64 requested but jax_enable_x64 is disabled.",
            iterations=0,
            warmup=0,
            environment={"derivative_backend": "jax_jacfwd"},
        )

    parameters = jnp.ones((dimensions,), dtype=jnp.float64)
    reference_diagonal = [float(index + 1) for index in range(dimensions)]

    def residuals(values):
        weights = jnp.arange(1, dimensions + 1, dtype=jnp.float64)
        return weights * values

    jacobian_function = jax.jit(jax.jacfwd(residuals))
    start = time.perf_counter()
    matrix = jacobian_function(parameters).block_until_ready()
    elapsed = time.perf_counter() - start
    matrix_list = [[float(value) for value in row] for row in matrix.tolist()]
    checksum = sum(sum(row) for row in matrix_list)
    reference = [
        [reference_diagonal[row] if row == column else 0.0 for column in range(dimensions)]
        for row in range(dimensions)
    ]
    max_abs_error = _max_matrix_abs_error(matrix_list, reference)

    return BenchmarkResult(
        name="jax_autodiff_jacobian",
        backend="jax",
        status="ok",
        dtype="float64",
        input_size=dimensions,
        iterations=1,
        warmup=0,
        checksum=checksum,
        timing=BenchmarkTiming(elapsed, elapsed, elapsed),
        environment={
            "derivative_backend": "jax_jacfwd",
            "row_count": dimensions,
            "column_count": dimensions,
            "reference_max_abs_error": max_abs_error,
            "reference_tolerance": 1.0e-12,
            "device": str(matrix.device() if callable(getattr(matrix, "device", None)) else matrix.device),
            "jax_version": jax.__version__,
            "python_version": platform.python_version(),
        },
    )


def run_optimizer_scaling_benchmark(*, max_dimensions: int = 4) -> BenchmarkResult:
    """Run deterministic local optimizer scaling smoke cases.

    Args:
        max_dimensions: Maximum parameter count to run, starting at one.

    Returns:
        Benchmark result summarizing objective evaluations by dimension.
    """
    _positive_int(max_dimensions, "max_dimensions")
    evaluations_by_dimension: dict[str, int] = {}
    status_by_dimension: dict[str, str] = {}
    objective_by_dimension: dict[str, float] = {}
    max_error_by_dimension: dict[str, float] = {}
    checksum = 0.0
    start = time.perf_counter()
    for dimensions in range(1, max_dimensions + 1):
        result = run_local_optimizer_benchmark(dimensions=dimensions)
        evaluations_by_dimension[str(dimensions)] = int(result.environment["function_evaluations"])
        status_by_dimension[str(dimensions)] = str(result.environment["status"])
        objective_by_dimension[str(dimensions)] = float(result.environment["final_objective"])
        max_error_by_dimension[str(dimensions)] = float(result.environment["max_abs_parameter_error"])
        checksum += float(result.checksum or 0.0)
    elapsed = time.perf_counter() - start

    return BenchmarkResult(
        name="local_optimizer_scaling",
        backend="python",
        status="ok",
        dtype="float64",
        input_size=max_dimensions,
        iterations=max_dimensions,
        warmup=0,
        checksum=checksum,
        timing=BenchmarkTiming(elapsed, elapsed, elapsed),
        environment={
            "evaluations_by_dimension": evaluations_by_dimension,
            "status_by_dimension": status_by_dimension,
            "objective_by_dimension": objective_by_dimension,
            "max_abs_parameter_error_by_dimension": max_error_by_dimension,
            "residual_length_by_dimension": {str(dimension): dimension for dimension in range(1, max_dimensions + 1)},
            "python_version": platform.python_version(),
        },
    )


def run_global_multistart_benchmark(*, dimensions: int = 2, start_count: int = 3) -> BenchmarkResult:
    """Run a deterministic multi-start global optimization smoke benchmark.

    Args:
        dimensions: Number of quadratic parameters.
        start_count: Number of generated starts.

    Returns:
        Benchmark result with convergence and parameter-error metrics.
    """
    _positive_int(dimensions, "dimensions")
    _positive_int(start_count, "start_count")
    target = tuple(float(index + 1) for index in range(dimensions))
    bounds = tuple(BoundTransform(lower=-10.0, upper=max(10.0, float(dimensions) + 1.0)) for _ in range(dimensions))

    def objective(parameters: tuple[float, ...]):
        return least_squares_evaluation(parameters, [value - expected for value, expected in zip(parameters, target, strict=True)])

    start = time.perf_counter()
    report = multi_start_minimize(
        objective,
        bounds=bounds,
        options=MultiStartOptions(
            start_count=start_count,
            seed=0,
            local_options=LocalOptimizerOptions(max_iterations=120, initial_step=1.0, tolerance=1.0e-6),
        ),
    )
    elapsed = time.perf_counter() - start
    errors = parameter_error_metrics(report.best_report.parameters, target)
    total_evaluations = sum(local_report.evaluations for local_report in report.reports)
    converged_count = sum(1 for local_report in report.reports if local_report.converged)

    return BenchmarkResult(
        name="global_multistart_quadratic",
        backend="python",
        status="ok",
        dtype="float64",
        input_size=dimensions,
        iterations=start_count,
        warmup=0,
        checksum=sum(report.best_report.parameters) + report.best_report.objective_value,
        timing=BenchmarkTiming(elapsed, elapsed, elapsed),
        environment={
            "status": report.status,
            "best_status": report.best_report.status,
            "best_converged": report.best_report.converged,
            "best_objective": report.best_report.objective_value,
            "total_function_evaluations": total_evaluations,
            "success_rate": converged_count / float(len(report.reports)),
            "candidate_statuses": [local_report.status for local_report in report.reports],
            "candidate_objectives": [local_report.objective_value for local_report in report.reports],
            "start_count": start_count,
            "max_abs_parameter_error": errors["max_abs_error"],
            "rms_parameter_error": errors["rms_error"],
            "python_version": platform.python_version(),
        },
    )


def _positive_int(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value!r}.")


def _max_matrix_abs_error(left: list[list[float]], right: list[list[float]]) -> float:
    if len(left) != len(right):
        raise ValueError("matrix row counts must match.")
    maximum = 0.0
    for row_index, (left_row, right_row) in enumerate(zip(left, right, strict=True)):
        if len(left_row) != len(right_row):
            raise ValueError(f"matrix row {row_index} lengths must match.")
        for left_value, right_value in zip(left_row, right_row, strict=True):
            maximum = max(maximum, abs(left_value - right_value))
    return maximum
