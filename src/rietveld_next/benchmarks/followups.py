"""Deterministic benchmark follow-up helpers.

This module contains small smoke fixtures for benchmark follow-up issues that
need machine-readable records without adding optional dependencies or expensive
default workloads.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import math
from pathlib import Path
import platform
import statistics
import subprocess
import time
from typing import Any

from rietveld_next.benchmarks.results import BenchmarkResult, BenchmarkTiming, skipped_benchmark
from rietveld_next.hpc.scheduler import JobSpec, LocalParallelBatchRunner, summarize_results
from rietveld_next.optimization.uncertainty import correlation_from_covariance, covariance_from_normal_matrix
from rietveld_next.workflows.replay import WorkflowAction, WorkflowStep, replay_workflow


def rust_gaussian_profile_skipped_benchmark(
    *,
    input_size: int = 256,
    peak_count: int = 3,
    iterations: int = 5,
    warmup: int = 1,
) -> BenchmarkResult:
    """Return a structured skipped record for the Rust Gaussian benchmark.

    Args:
        input_size: Intended number of profile-axis samples.
        peak_count: Intended number of Gaussian peaks in the fixture.
        iterations: Intended measured steady-state iterations.
        warmup: Intended unmeasured warmup iterations.

    Returns:
        Skipped benchmark result documenting the Rust fixture contract.

    Raises:
        ValueError: If sizing inputs are invalid.
    """

    _positive_int(input_size, "input_size")
    _positive_int(peak_count, "peak_count")
    _positive_int(iterations, "iterations")
    _nonnegative_int(warmup, "warmup")

    return skipped_benchmark(
        name="gaussian_profile",
        backend="rust",
        dtype="float64",
        input_size=input_size,
        iterations=iterations,
        warmup=warmup,
        reason="Rust Gaussian profile backend is not available in this Python-only smoke fixture.",
        environment={
            **_base_environment(seed=0, issue_numbers=[292]),
            "axis_unit": "degree_two_theta",
            "device": "cpu",
            "live_optional_backend": False,
            "peak_count": peak_count,
            "kernel_contract": {
                "input_validation": "axis, centers, amplitudes, and sigmas lengths must be explicit",
                "dtype": "f64",
                "allocation_policy": "no avoidable allocation inside peak loop",
            },
        },
    )


def run_parametric_refinement_benchmark(
    *,
    point_count: int = 6,
    iterations: int = 1,
    warmup: int = 0,
    seed: int = 0,
) -> BenchmarkResult:
    """Benchmark a deterministic linear parametric refinement fixture.

    Args:
        point_count: Number of synthetic external-variable points.
        iterations: Number of measured linear-fit runs.
        warmup: Number of unmeasured runs.
        seed: Non-negative deterministic fixture seed.

    Returns:
        Benchmark result comparing parametric and sequential estimates.

    Raises:
        ValueError: If inputs are invalid.
    """

    _positive_int(point_count, "point_count")
    if point_count < 2:
        raise ValueError("point_count must be at least 2 for a linear function model.")
    _positive_int(iterations, "iterations")
    _nonnegative_int(warmup, "warmup")
    _nonnegative_int(seed, "seed")

    variables, observations, truth = _parametric_fixture(point_count=point_count, seed=seed)
    for _ in range(warmup):
        _fit_line(variables, observations)

    measurements: list[float] = []
    coefficients: tuple[float, float] | None = None
    for _ in range(iterations):
        start = time.perf_counter()
        coefficients = _fit_line(variables, observations)
        measurements.append(time.perf_counter() - start)
    assert coefficients is not None

    intercept, slope = coefficients
    parametric_predictions = tuple(intercept + slope * variable for variable in variables)
    sequential_predictions = observations
    parametric_errors = _error_metrics(parametric_predictions, truth)
    sequential_errors = _error_metrics(sequential_predictions, truth)
    coefficient_errors = {
        "intercept_angstrom": intercept - (4.0 + 0.001 * float(seed)),
        "slope_angstrom_per_k": slope - 2.0e-4,
    }

    return BenchmarkResult(
        name="workflow.parametric_refinement.python.small.synthetic",
        backend="python",
        status="ok",
        dtype="float64",
        input_size=point_count,
        iterations=iterations,
        warmup=warmup,
        checksum=_sequence_checksum(parametric_predictions),
        timing=_timing_from_measurements(measurements),
        environment={
            **_base_environment(seed=seed, issue_numbers=[306]),
            "external_variables": {"temperature_k": list(variables)},
            "function_model": {
                "parameter": "lattice_a_angstrom",
                "form": "intercept + slope * temperature_k",
                "coefficient_units": {
                    "intercept": "angstrom",
                    "slope": "angstrom_per_kelvin",
                },
            },
            "coefficient_errors": coefficient_errors,
            "parameter_function_error": parametric_errors,
            "sequential_baseline_error": sequential_errors,
            "comparison_dataset": "common_synthetic_temperature_series",
        },
    )


def run_batch_throughput_benchmark(
    *,
    job_count: int = 8,
    worker_count: int = 2,
    iterations: int = 1,
    warmup: int = 0,
    seed: int = 0,
) -> BenchmarkResult:
    """Benchmark local deterministic batch throughput with fake refinements.

    Args:
        job_count: Number of independent synthetic refinement jobs.
        worker_count: Number of local worker threads.
        iterations: Number of measured batch runs.
        warmup: Number of unmeasured batch runs.
        seed: Non-negative deterministic fixture seed.

    Returns:
        Benchmark result with throughput and success/failure counts.

    Raises:
        ValueError: If sizing inputs are invalid.
    """

    _positive_int(job_count, "job_count")
    _positive_int(worker_count, "worker_count")
    _positive_int(iterations, "iterations")
    _nonnegative_int(warmup, "warmup")
    _nonnegative_int(seed, "seed")
    jobs = _batch_jobs(job_count=job_count, seed=seed)
    runner = LocalParallelBatchRunner({"refine": _synthetic_batch_refinement}, max_workers=worker_count)

    for _ in range(warmup):
        runner.run(jobs)

    measurements: list[float] = []
    final_summary: Mapping[str, int] = {}
    final_checksum = 0.0
    for _ in range(iterations):
        start = time.perf_counter()
        batch = runner.run(jobs)
        measurements.append(time.perf_counter() - start)
        final_summary = summarize_results(batch.results)
        final_checksum = sum(float(result.output["objective"]) for result in batch.results if result.output)

    total_wall_time = sum(measurements)
    success_count = int(final_summary.get("ok", 0))
    failure_count = job_count - success_count
    return BenchmarkResult(
        name="workflow.batch_throughput.python.small.local",
        backend="python",
        status="ok",
        dtype="float64",
        input_size=job_count,
        iterations=iterations,
        warmup=warmup,
        checksum=final_checksum,
        timing=_timing_from_measurements(measurements),
        environment={
            **_base_environment(seed=seed, issue_numbers=[307]),
            "job_count": job_count,
            "worker_count": worker_count,
            "success_count": success_count,
            "failure_count": failure_count,
            "refinements_per_second": (job_count * iterations) / max(total_wall_time, 1.0e-12),
            "total_wall_time_seconds": total_wall_time,
            "large_cases_opt_in_only": True,
            "scheduler": "local-parallel-fake-adapter",
        },
    )


def run_tof_calibration_refinement_benchmark(
    *,
    bank_count: int = 2,
    peak_count: int = 4,
    iterations: int = 1,
    warmup: int = 0,
    seed: int = 0,
) -> BenchmarkResult:
    """Benchmark synthetic TOF calibration parameter recovery.

    Args:
        bank_count: Number of synthetic detector banks.
        peak_count: Number of known d-spacing peaks per bank.
        iterations: Number of measured fit passes.
        warmup: Number of unmeasured fit passes.
        seed: Non-negative deterministic fixture seed.

    Returns:
        Benchmark result with convergence and parameter errors by bank.

    Raises:
        ValueError: If inputs are invalid.
    """

    _positive_int(bank_count, "bank_count")
    _positive_int(peak_count, "peak_count")
    if peak_count < 3:
        raise ValueError("peak_count must be at least 3 for quadratic TOF calibration.")
    _positive_int(iterations, "iterations")
    _nonnegative_int(warmup, "warmup")
    _nonnegative_int(seed, "seed")

    fixtures = _tof_bank_fixtures(bank_count=bank_count, peak_count=peak_count, seed=seed)
    for _ in range(warmup):
        _fit_tof_banks(fixtures)

    measurements: list[float] = []
    fitted: list[dict[str, Any]] | None = None
    for _ in range(iterations):
        start = time.perf_counter()
        fitted = _fit_tof_banks(fixtures)
        measurements.append(time.perf_counter() - start)
    assert fitted is not None

    max_error = max(float(bank["max_abs_parameter_error"]) for bank in fitted)
    return BenchmarkResult(
        name="tof.calibration_refinement.python.small.synthetic",
        backend="python",
        status="ok",
        dtype="float64",
        input_size=bank_count * peak_count,
        iterations=iterations,
        warmup=warmup,
        checksum=_mapping_checksum({"banks": fitted}),
        timing=_timing_from_measurements(measurements),
        environment={
            **_base_environment(seed=seed, issue_numbers=[309]),
            "bank_count": bank_count,
            "peak_count_per_bank": peak_count,
            "axis_units": {"d_spacing": "angstrom", "tof": "microsecond"},
            "convergence_status": "ok" if max_error <= 1.0e-9 else "warning",
            "parameter_error_tolerance": 1.0e-9,
            "max_abs_parameter_error": max_error,
            "parameter_errors_by_bank": fitted,
            "large_fixture_opt_in_only": True,
        },
    )


def run_edxrd_calibration_workflow_benchmark(
    *,
    peak_count: int = 5,
    polynomial_order: int = 2,
    iterations: int = 1,
    warmup: int = 0,
    seed: int = 0,
) -> BenchmarkResult:
    """Benchmark synthetic channel-to-energy EDXRD calibration.

    Args:
        peak_count: Number of synthetic standard peaks.
        polynomial_order: Polynomial order for channel-to-energy calibration.
        iterations: Number of measured fit passes.
        warmup: Number of unmeasured fit passes.
        seed: Non-negative deterministic fixture seed.

    Returns:
        Benchmark result with coefficient errors and standard-peak metadata.

    Raises:
        ValueError: If inputs are invalid.
    """

    _positive_int(peak_count, "peak_count")
    _nonnegative_int(polynomial_order, "polynomial_order")
    if polynomial_order != 2:
        raise ValueError("polynomial_order must be 2 for the deterministic smoke fixture.")
    if peak_count < polynomial_order + 1:
        raise ValueError("peak_count must provide at least polynomial_order + 1 peaks.")
    _positive_int(iterations, "iterations")
    _nonnegative_int(warmup, "warmup")
    _nonnegative_int(seed, "seed")

    channels, energies, reference = _edxrd_fixture(peak_count=peak_count, seed=seed)
    for _ in range(warmup):
        _fit_polynomial(channels, energies, order=polynomial_order)

    measurements: list[float] = []
    coefficients: tuple[float, ...] | None = None
    for _ in range(iterations):
        start = time.perf_counter()
        coefficients = _fit_polynomial(channels, energies, order=polynomial_order)
        measurements.append(time.perf_counter() - start)
    assert coefficients is not None

    coefficient_errors = {
        f"c{index}": coefficients[index] - reference[index]
        for index in range(len(coefficients))
    }
    max_error = max(abs(error) for error in coefficient_errors.values())

    return BenchmarkResult(
        name="edxrd.calibration_workflow.python.small.synthetic",
        backend="python",
        status="ok",
        dtype="float64",
        input_size=peak_count,
        iterations=iterations,
        warmup=warmup,
        checksum=_sequence_checksum(coefficients),
        timing=_timing_from_measurements(measurements),
        environment={
            **_base_environment(seed=seed, issue_numbers=[313]),
            "polynomial_order": polynomial_order,
            "calibration_model": "energy_kev = c0 + c1 * channel + c2 * channel^2",
            "coefficient_units": ["kev", "kev_per_channel", "kev_per_channel_squared"],
            "coefficient_errors": coefficient_errors,
            "max_abs_coefficient_error": max_error,
            "standard_peaks": [
                {"channel": channels[index], "energy_kev": energies[index]}
                for index in range(peak_count)
            ],
            "normal_ci_fixture": "small_exact_synthetic_standard",
        },
    )


def zarr_profile_array_io_skipped_benchmark(
    *,
    profile_count: int = 3,
    point_count: int = 16,
    chunk_shape: tuple[int, int] = (1, 16),
) -> BenchmarkResult:
    """Return a skipped Zarr IO fixture record without importing Zarr.

    Args:
        profile_count: Number of synthetic profiles in the intended array.
        point_count: Number of points per profile.
        chunk_shape: Intended two-dimensional chunk shape.

    Returns:
        Skipped benchmark result with array and chunk metadata.

    Raises:
        ValueError: If fixture dimensions are invalid.
    """

    _positive_int(profile_count, "profile_count")
    _positive_int(point_count, "point_count")
    _chunk_shape(chunk_shape)
    return skipped_benchmark(
        name="storage.zarr_profile_array_io.python.small.optional",
        backend="zarr",
        dtype="float64",
        input_size=profile_count * point_count,
        reason="Zarr is optional and is not imported by the default smoke fixture.",
        environment={
            **_base_environment(seed=0, issue_numbers=[315]),
            "array_shape": [profile_count, point_count],
            "chunk_shape": list(chunk_shape),
            "compression": "not_configured_without_optional_backend",
            "read_runtime_seconds": None,
            "write_runtime_seconds": None,
            "filesystem_semantics": "local smoke metadata; object-store behavior must be measured by opt-in backend runs",
            "live_optional_backend": False,
        },
    )


def parquet_result_table_io_skipped_benchmark(
    *,
    row_count: int = 4,
    column_count: int = 5,
) -> BenchmarkResult:
    """Return a skipped Parquet IO fixture record without Arrow dependencies.

    Args:
        row_count: Number of synthetic result rows in the intended table.
        column_count: Number of columns in the result-table schema.

    Returns:
        Skipped benchmark result with table metadata.

    Raises:
        ValueError: If table dimensions are invalid.
    """

    _positive_int(row_count, "row_count")
    _positive_int(column_count, "column_count")
    return skipped_benchmark(
        name="storage.parquet_result_table_io.python.small.optional",
        backend="parquet",
        dtype="table",
        input_size=row_count,
        reason="Parquet/Arrow dependencies are optional and are not imported by the default smoke fixture.",
        environment={
            **_base_environment(seed=0, issue_numbers=[316]),
            "row_count": row_count,
            "column_count": column_count,
            "file_size_bytes": None,
            "read_runtime_seconds": None,
            "write_runtime_seconds": None,
            "schema_columns": [
                "run_id",
                "phase_id",
                "parameter",
                "value",
                "uncertainty",
            ][:column_count],
            "live_optional_backend": False,
        },
    )


def run_covariance_correlation_computation_benchmark(
    *,
    parameter_count: int = 3,
    iterations: int = 1,
    warmup: int = 0,
    seed: int = 0,
) -> BenchmarkResult:
    """Benchmark covariance and correlation diagnostics on a small matrix.

    Args:
        parameter_count: Number of synthetic parameters.
        iterations: Number of measured covariance/correlation runs.
        warmup: Number of unmeasured runs.
        seed: Non-negative deterministic fixture seed.

    Returns:
        Benchmark result with status, condition estimate, and matrix checks.

    Raises:
        ValueError: If sizing inputs are invalid.
    """

    _positive_int(parameter_count, "parameter_count")
    _positive_int(iterations, "iterations")
    _nonnegative_int(warmup, "warmup")
    _nonnegative_int(seed, "seed")

    normal_matrix = _positive_definite_normal_matrix(parameter_count=parameter_count, seed=seed)
    labels = tuple(f"p{index}" for index in range(parameter_count))
    units = tuple("angstrom" if index == 0 else "dimensionless" for index in range(parameter_count))
    for _ in range(warmup):
        covariance_from_normal_matrix(normal_matrix, parameter_labels=labels, parameter_units=units)

    measurements: list[float] = []
    covariance = None
    correlation = None
    for _ in range(iterations):
        start = time.perf_counter()
        covariance = covariance_from_normal_matrix(
            normal_matrix,
            parameter_labels=labels,
            parameter_units=units,
        )
        if covariance.covariance is None:
            raise RuntimeError("well-conditioned synthetic matrix unexpectedly failed covariance solve")
        correlation = correlation_from_covariance(covariance.covariance, parameter_labels=labels)
        measurements.append(time.perf_counter() - start)
    assert covariance is not None and correlation is not None

    singular = covariance_from_normal_matrix(
        [[1.0, 1.0], [1.0, 1.0]],
        parameter_labels=("singular_a", "singular_b"),
    )
    covariance_values = covariance.covariance or []
    correlation_values = correlation.correlation or []

    return BenchmarkResult(
        name="diagnostics.covariance_correlation.python.small.synthetic",
        backend="python",
        status="ok",
        dtype="float64",
        input_size=parameter_count,
        iterations=iterations,
        warmup=warmup,
        checksum=_mapping_checksum({"covariance": covariance_values, "correlation": correlation_values}),
        timing=_timing_from_measurements(measurements),
        environment={
            **_base_environment(seed=seed, issue_numbers=[319]),
            "matrix_dimensions": [parameter_count, parameter_count],
            "sparsity": _matrix_sparsity(normal_matrix),
            "condition_number": covariance.condition_number,
            "covariance_status": covariance.status,
            "correlation_status": correlation.status,
            "parameter_labels": list(covariance.parameter_labels),
            "parameter_units": list(covariance.parameter_units),
            "symmetry_max_abs_error": _symmetry_max_abs_error(covariance_values),
            "diagonal_positive": all(covariance_values[index][index] > 0.0 for index in range(parameter_count)),
            "high_correlation_count": len(correlation.high_correlations),
            "singular_case_status": singular.status,
            "singular_case_warnings": list(singular.warnings),
        },
    )


def validate_agent_action_log(actions: Sequence[WorkflowAction]) -> dict[str, Any]:
    """Validate replay action provenance records.

    Args:
        actions: Workflow replay actions to validate.

    Returns:
        Structured validation report with deterministic error records.
    """

    errors: list[dict[str, Any]] = []
    expected_sequence = 0
    seen_step_ids: set[str] = set()
    for action in actions:
        if action.sequence != expected_sequence:
            errors.append(
                {
                    "code": "non_contiguous_sequence",
                    "sequence": action.sequence,
                    "expected": expected_sequence,
                }
            )
        expected_sequence += 1
        if action.step_id in seen_step_ids:
            errors.append({"code": "duplicate_step_id", "step_id": action.step_id})
        seen_step_ids.add(action.step_id)
        provenance = action.inputs.get("provenance")
        if not isinstance(provenance, Mapping):
            errors.append({"code": "missing_provenance", "step_id": action.step_id})
        elif not provenance.get("source"):
            errors.append({"code": "missing_provenance_source", "step_id": action.step_id})
        if action.status == "ok" and action.output is None:
            errors.append({"code": "missing_output", "step_id": action.step_id})
        if action.status == "error" and not action.error:
            errors.append({"code": "missing_error_message", "step_id": action.step_id})
    return {
        "status": "ok" if not errors else "error",
        "action_count": len(actions),
        "success_count": sum(1 for action in actions if action.status == "ok"),
        "failure_count": sum(1 for action in actions if action.status == "error"),
        "errors": errors,
    }


def run_agent_replay_provenance_validation_benchmark(
    *,
    action_count: int = 4,
    iterations: int = 1,
    warmup: int = 0,
    seed: int = 0,
) -> BenchmarkResult:
    """Benchmark deterministic agent action replay and provenance validation.

    Args:
        action_count: Number of valid replay actions in the fixture.
        iterations: Number of measured replay/validation passes.
        warmup: Number of unmeasured passes.
        seed: Non-negative deterministic fixture seed.

    Returns:
        Benchmark result with replay counts and invalid-log diagnostics.

    Raises:
        ValueError: If sizing inputs are invalid.
    """

    _positive_int(action_count, "action_count")
    _positive_int(iterations, "iterations")
    _nonnegative_int(warmup, "warmup")
    _nonnegative_int(seed, "seed")
    steps = _agent_replay_steps(action_count=action_count, seed=seed)
    handlers = {"record_observation": _record_agent_observation}

    for _ in range(warmup):
        result = replay_workflow(steps, handlers)
        validate_agent_action_log(result.actions)

    measurements: list[float] = []
    validation_report: dict[str, Any] | None = None
    final_actions: tuple[WorkflowAction, ...] = ()
    for _ in range(iterations):
        start = time.perf_counter()
        result = replay_workflow(steps, handlers)
        validation_report = validate_agent_action_log(result.actions)
        measurements.append(time.perf_counter() - start)
        final_actions = result.actions
    assert validation_report is not None

    invalid_actions = (
        WorkflowAction(
            sequence=0,
            step_id="invalid_000",
            tool="record_observation",
            inputs={},
            status="ok",
            output={"accepted": True},
        ),
    )
    invalid_report = validate_agent_action_log(invalid_actions)

    return BenchmarkResult(
        name="ai.agent_replay_provenance_validation.python.small.synthetic",
        backend="python",
        status="ok",
        dtype="json",
        input_size=action_count,
        iterations=iterations,
        warmup=warmup,
        checksum=_mapping_checksum({"validation": validation_report, "actions": [_action_to_dict(action) for action in final_actions]}),
        timing=_timing_from_measurements(measurements),
        environment={
            **_base_environment(seed=seed, issue_numbers=[321]),
            "actions_replayed": validation_report["action_count"],
            "replay_success_count": validation_report["success_count"],
            "replay_failure_count": validation_report["failure_count"],
            "validation_status": validation_report["status"],
            "validation_error_count": len(validation_report["errors"]),
            "invalid_log_status": invalid_report["status"],
            "invalid_log_errors": invalid_report["errors"],
            "deterministic_replay": True,
            "llm_calls_included": False,
        },
    )


def compare_benchmark_regression_baseline(
    current_results: Sequence[Mapping[str, Any]],
    baseline_results: Sequence[Mapping[str, Any]],
    *,
    threshold_percent: float = 10.0,
    fail_on_regression: bool = False,
) -> dict[str, Any]:
    """Compare current benchmark timings against a baseline.

    Args:
        current_results: Current benchmark result dictionaries.
        baseline_results: Baseline benchmark result dictionaries.
        threshold_percent: Allowed positive runtime increase in percent.
        fail_on_regression: Whether threshold breaches should report
            ``"fail"`` instead of the default ``"warn"``.

    Returns:
        JSON-compatible comparison report.

    Raises:
        ValueError: If threshold or result records are invalid.
    """

    threshold = _positive_float(threshold_percent, "threshold_percent")
    baseline_by_name = {_benchmark_name(result): result for result in baseline_results}
    comparisons: list[dict[str, Any]] = []
    missing_baselines: list[str] = []

    for current in current_results:
        name = _benchmark_name(current)
        baseline = baseline_by_name.get(name)
        if baseline is None:
            missing_baselines.append(name)
            continue
        current_seconds = _median_seconds(current, "current")
        baseline_seconds = _median_seconds(baseline, "baseline")
        if baseline_seconds == 0.0:
            percent_change = 0.0 if current_seconds == 0.0 else math.inf
        else:
            percent_change = ((current_seconds - baseline_seconds) / baseline_seconds) * 100.0
        regression = percent_change > threshold
        comparisons.append(
            {
                "name": name,
                "baseline_median_seconds": baseline_seconds,
                "current_median_seconds": current_seconds,
                "percent_change": percent_change,
                "threshold_percent": threshold,
                "regression": regression,
                "status": "regression" if regression else "ok",
            }
        )

    regression_count = sum(1 for comparison in comparisons if comparison["regression"])
    status = "ok"
    if regression_count:
        status = "fail" if fail_on_regression else "warn"
    return {
        "schema_version": "benchmark-baseline-comparison-v1",
        "status": status,
        "fail_on_regression": fail_on_regression,
        "threshold_percent": threshold,
        "comparison_count": len(comparisons),
        "regression_count": regression_count,
        "missing_baselines": sorted(missing_baselines),
        "comparisons": comparisons,
        "baseline_environment": {
            "benchmark_version": "benchmark-result-v1",
            "comparison_policy": "warn_by_default",
        },
    }


def run_benchmark_regression_baseline_comparison(
    *,
    threshold_percent: float = 10.0,
    fail_on_regression: bool = False,
) -> BenchmarkResult:
    """Run a small deterministic baseline-comparison smoke benchmark.

    Args:
        threshold_percent: Allowed positive runtime increase in percent.
        fail_on_regression: Whether threshold breaches should be failures.

    Returns:
        Benchmark result containing a baseline comparison report.
    """

    current = _baseline_fixture_result("workflow.batch_throughput.python.small.local", 0.011)
    baseline = _baseline_fixture_result("workflow.batch_throughput.python.small.local", 0.010)
    start = time.perf_counter()
    report = compare_benchmark_regression_baseline(
        [current],
        [baseline],
        threshold_percent=threshold_percent,
        fail_on_regression=fail_on_regression,
    )
    elapsed = time.perf_counter() - start
    return BenchmarkResult(
        name="infrastructure.benchmark_regression_baseline_comparison.python.small.synthetic",
        backend="python",
        status="ok",
        dtype="json",
        input_size=1,
        iterations=1,
        warmup=0,
        checksum=_mapping_checksum(report),
        timing=BenchmarkTiming(elapsed, elapsed, elapsed, compile_seconds=None),
        environment={
            **_base_environment(seed=0, issue_numbers=[324]),
            "comparison_report": report,
            "default_behavior": "warn" if not fail_on_regression else "fail",
        },
    )


def benchmark_documentation_hub_payload() -> dict[str, Any]:
    """Return a deterministic benchmark documentation hub payload.

    Returns:
        JSON-compatible documentation inventory for benchmark users and
        contributors. It is intentionally data-only because this follow-up is
        scoped away from editing repository documentation files.
    """

    return {
        "schema_version": "benchmark-documentation-hub-v1",
        "issue_numbers": [326],
        "title": "Benchmark documentation hub",
        "commands": {
            "quick": "PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next/benchmarks -p 'test*.py'",
            "medium": "PYTHONPATH=src python3 -B -m unittest src/rietveld_next/benchmarks/tests/test_followups.py",
            "large_opt_in": "Run benchmark CLIs with explicit size flags only; large cases are not default CI workloads.",
        },
        "sections": [
            "benchmark families",
            "result schema",
            "taxonomy",
            "quick medium and opt-in large runs",
            "JAX compile time versus steady-state timing",
            "GPU caveats",
            "Rust serial and parallel variants",
            "CI skip policy",
            "known limitations",
            "contributor guide",
        ],
        "links": {
            "result_schema": "rietveld_next.benchmarks.results.benchmark_result_schema",
            "taxonomy": "rietveld_next.benchmarks.taxonomy",
            "followup_fixtures": "rietveld_next.benchmarks.followups",
        },
        "ci_policy": {
            "default": "smoke_only",
            "optional_backends": ["jax", "rust", "zarr", "parquet"],
            "skip_records_are_machine_readable": True,
        },
        "limitations": [
            "Optional backend records in this module do not perform live backend IO.",
            "Synthetic fixtures document assumptions and are not validation claims against facility data.",
        ],
    }


def run_benchmark_documentation_hub_payload_benchmark() -> BenchmarkResult:
    """Return a smoke record for generating the documentation hub payload.

    Returns:
        Benchmark result whose environment contains the documentation payload.
    """

    start = time.perf_counter()
    payload = benchmark_documentation_hub_payload()
    elapsed = time.perf_counter() - start
    return BenchmarkResult(
        name="infrastructure.benchmark_documentation_hub_payload.python.small.synthetic",
        backend="python",
        status="ok",
        dtype="json",
        input_size=len(payload["sections"]),
        iterations=1,
        warmup=0,
        checksum=_mapping_checksum(payload),
        timing=BenchmarkTiming(elapsed, elapsed, elapsed, compile_seconds=None),
        environment={
            **_base_environment(seed=0, issue_numbers=[326]),
            "documentation_payload": payload,
        },
    )


def _parametric_fixture(*, point_count: int, seed: int) -> tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]:
    intercept = 4.0 + 0.001 * float(seed)
    slope = 2.0e-4
    temperatures = tuple(300.0 + 5.0 * float(index) for index in range(point_count))
    truth = tuple(intercept + slope * temperature for temperature in temperatures)
    residual_pattern = (-2.0e-5, 0.0, 2.0e-5)
    observations = tuple(
        value + residual_pattern[index % len(residual_pattern)]
        for index, value in enumerate(truth)
    )
    return temperatures, observations, truth


def _fit_line(x_values: Sequence[float], y_values: Sequence[float]) -> tuple[float, float]:
    if len(x_values) != len(y_values):
        raise ValueError("x_values and y_values must have the same length.")
    count = len(x_values)
    if count < 2:
        raise ValueError("at least two points are required for a line fit.")
    mean_x = sum(x_values) / count
    mean_y = sum(y_values) / count
    denominator = sum((x - mean_x) ** 2 for x in x_values)
    if denominator <= 0.0:
        raise ValueError("x_values must contain variation for a line fit.")
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values, strict=True)) / denominator
    intercept = mean_y - slope * mean_x
    return intercept, slope


def _batch_jobs(*, job_count: int, seed: int) -> tuple[JobSpec, ...]:
    return tuple(
        JobSpec(
            job_id=f"batch_{index:04d}",
            command="refine",
            payload={
                "index": index,
                "target": float(index + seed + 1),
                "initial": 0.0,
            },
            resources={"cpus": 1},
            metadata={"fixture": "batch_throughput", "seed": seed},
        )
        for index in range(job_count)
    )


def _synthetic_batch_refinement(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    target = _finite_float(payload["target"], "target")
    initial = _finite_float(payload["initial"], "initial")
    estimate = target + 0.125 * (initial - target)
    objective = (estimate - target) ** 2
    return {
        "estimate": estimate,
        "objective": objective,
        "status": "ok",
    }


def _tof_bank_fixtures(*, bank_count: int, peak_count: int, seed: int) -> list[dict[str, Any]]:
    d_spacings = tuple(0.8 + 0.25 * float(index) for index in range(peak_count))
    fixtures = []
    for bank_index in range(bank_count):
        reference = (
            5.0 + float(seed) + 0.5 * bank_index,
            1200.0 + 25.0 * bank_index,
            0.12 + 0.01 * bank_index,
        )
        tof = tuple(
            reference[0] + reference[1] * d_spacing + reference[2] * d_spacing * d_spacing
            for d_spacing in d_spacings
        )
        fixtures.append(
            {
                "bank_id": f"bank_{bank_index}",
                "d_spacings": d_spacings,
                "tof_microseconds": tof,
                "reference": reference,
            }
        )
    return fixtures


def _fit_tof_banks(fixtures: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    reports = []
    for fixture in fixtures:
        d_spacings = tuple(float(value) for value in fixture["d_spacings"])
        tof_values = tuple(float(value) for value in fixture["tof_microseconds"])
        fitted = _fit_polynomial(d_spacings, tof_values, order=2)
        reference = tuple(float(value) for value in fixture["reference"])
        errors = tuple(value - expected for value, expected in zip(fitted, reference, strict=True))
        reports.append(
            {
                "bank_id": str(fixture["bank_id"]),
                "fitted_parameters": {
                    "zero_us": fitted[0],
                    "difc_us_per_angstrom": fitted[1],
                    "difa_us_per_angstrom_squared": fitted[2],
                },
                "parameter_errors": {
                    "zero_us": errors[0],
                    "difc_us_per_angstrom": errors[1],
                    "difa_us_per_angstrom_squared": errors[2],
                },
                "max_abs_parameter_error": max(abs(error) for error in errors),
            }
        )
    return reports


def _edxrd_fixture(*, peak_count: int, seed: int) -> tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]:
    coefficients = (1.5 + 0.01 * float(seed), 0.020, 1.0e-6)
    channels = tuple(100.0 + 60.0 * float(index) for index in range(peak_count))
    energies = tuple(
        coefficients[0] + coefficients[1] * channel + coefficients[2] * channel * channel
        for channel in channels
    )
    return channels, energies, coefficients


def _fit_polynomial(x_values: Sequence[float], y_values: Sequence[float], *, order: int) -> tuple[float, ...]:
    if len(x_values) != len(y_values):
        raise ValueError("x_values and y_values must have the same length.")
    if len(x_values) < order + 1:
        raise ValueError("not enough points for requested polynomial order.")
    normal = [
        [
            sum(float(x) ** (left + right) for x in x_values)
            for right in range(order + 1)
        ]
        for left in range(order + 1)
    ]
    rhs = [
        sum(float(y) * (float(x) ** left) for x, y in zip(x_values, y_values, strict=True))
        for left in range(order + 1)
    ]
    return tuple(_solve_linear_system(normal, rhs))


def _solve_linear_system(matrix: Sequence[Sequence[float]], rhs: Sequence[float]) -> list[float]:
    size = len(matrix)
    if size == 0 or len(rhs) != size:
        raise ValueError("linear system dimensions must match and be non-empty.")
    augmented = [list(row) + [float(rhs[index])] for index, row in enumerate(matrix)]
    for row in augmented:
        if len(row) != size + 1:
            raise ValueError("linear system matrix must be square.")

    for pivot_column in range(size):
        pivot_row = max(
            range(pivot_column, size),
            key=lambda row_index: abs(augmented[row_index][pivot_column]),
        )
        if abs(augmented[pivot_row][pivot_column]) <= 1.0e-14:
            raise ValueError("linear system is singular for the synthetic fit.")
        if pivot_row != pivot_column:
            augmented[pivot_column], augmented[pivot_row] = augmented[pivot_row], augmented[pivot_column]
        pivot = augmented[pivot_column][pivot_column]
        augmented[pivot_column] = [value / pivot for value in augmented[pivot_column]]
        for row_index in range(size):
            if row_index == pivot_column:
                continue
            factor = augmented[row_index][pivot_column]
            augmented[row_index] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row_index], augmented[pivot_column], strict=True)
            ]
    return [row[-1] for row in augmented]


def _positive_definite_normal_matrix(*, parameter_count: int, seed: int) -> list[list[float]]:
    matrix: list[list[float]] = []
    for row in range(parameter_count):
        matrix_row = []
        for column in range(parameter_count):
            if row == column:
                matrix_row.append(4.0 + float(row + seed))
            else:
                matrix_row.append(0.1 / float(abs(row - column) + 1))
        matrix.append(matrix_row)
    return matrix


def _agent_replay_steps(*, action_count: int, seed: int) -> tuple[WorkflowStep, ...]:
    return tuple(
        WorkflowStep(
            step_id=f"agent_step_{index:03d}",
            tool="record_observation",
            inputs={
                "scan_id": f"scan_{seed:02d}_{index:04d}",
                "value": float(index + seed),
                "provenance": {
                    "source": "synthetic_agent_replay_fixture",
                    "seed": seed,
                    "sequence": index,
                },
            },
        )
        for index in range(action_count)
    )


def _record_agent_observation(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    provenance = payload.get("provenance")
    if not isinstance(provenance, Mapping) or not provenance.get("source"):
        raise ValueError("provenance.source is required")
    return {
        "accepted": True,
        "scan_id": str(payload["scan_id"]),
        "value_checksum": _finite_float(payload["value"], "value") + float(provenance["sequence"]),
    }


def _baseline_fixture_result(name: str, median_seconds: float) -> dict[str, Any]:
    return {
        "schema_version": "benchmark-result-v1",
        "name": name,
        "status": "ok",
        "timing": {
            "median_seconds": median_seconds,
            "min_seconds": median_seconds,
            "max_seconds": median_seconds,
            "compile_seconds": None,
        },
        "environment": {
            "benchmark_version": "benchmark-result-v1",
            "python_version": platform.python_version(),
        },
    }


def _benchmark_name(result: Mapping[str, Any]) -> str:
    name = result.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError("benchmark result name must be a non-empty string.")
    return name


def _median_seconds(result: Mapping[str, Any], role: str) -> float:
    timing = result.get("timing")
    if not isinstance(timing, Mapping):
        raise ValueError(f"{role} result timing must be a mapping.")
    return _finite_nonnegative_float(timing.get("median_seconds"), f"{role}.timing.median_seconds")


def _action_to_dict(action: WorkflowAction) -> dict[str, Any]:
    return {
        "sequence": action.sequence,
        "step_id": action.step_id,
        "tool": action.tool,
        "inputs": dict(action.inputs),
        "status": action.status,
        "output": None if action.output is None else dict(action.output),
        "error": action.error,
    }


def _error_metrics(values: Sequence[float], reference: Sequence[float]) -> dict[str, float]:
    if len(values) != len(reference):
        raise ValueError("values and reference must have matching lengths.")
    errors = [value - expected for value, expected in zip(values, reference, strict=True)]
    return {
        "max_abs_error": max(abs(error) for error in errors),
        "rms_error": math.sqrt(sum(error * error for error in errors) / len(errors)),
    }


def _timing_from_measurements(measurements: Sequence[float]) -> BenchmarkTiming:
    if not measurements:
        raise ValueError("measurements must contain at least one runtime.")
    return BenchmarkTiming(
        median_seconds=statistics.median(measurements),
        min_seconds=min(measurements),
        max_seconds=max(measurements),
        compile_seconds=None,
    )


def _matrix_sparsity(matrix: Sequence[Sequence[float]]) -> float:
    total = sum(len(row) for row in matrix)
    zeros = sum(1 for row in matrix for value in row if value == 0.0)
    return zeros / float(total)


def _symmetry_max_abs_error(matrix: Sequence[Sequence[float]]) -> float:
    maximum = 0.0
    for row in range(len(matrix)):
        for column in range(row + 1, len(matrix)):
            maximum = max(maximum, abs(matrix[row][column] - matrix[column][row]))
    return maximum


def _sequence_checksum(values: Sequence[float]) -> float:
    return sum((index + 1) * float(value) for index, value in enumerate(values))


def _mapping_checksum(value: Mapping[str, Any]) -> float:
    return float(
        sum(
            (index + 1) * ord(character)
            for index, character in enumerate(json.dumps(value, sort_keys=True, separators=(",", ":")))
        )
    )


def _base_environment(*, seed: int, issue_numbers: list[int]) -> dict[str, Any]:
    return {
        "benchmark_issue_numbers": issue_numbers,
        "git_commit": _git_commit_or_none(),
        "platform_machine": platform.machine(),
        "platform_system": platform.system(),
        "python_version": platform.python_version(),
        "seed": seed,
        "timing_model": {
            "compile_seconds": "none for dependency-free Python fixtures; optional backends report separately",
            "steady_state": "median/min/max measured wall time from perf_counter",
            "warmup": "unmeasured fixture runs before steady-state timing",
        },
    }


def _git_commit_or_none() -> str | None:
    repo_root = Path(__file__).resolve().parents[3]
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            check=False,
            text=True,
            timeout=1.0,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    commit = completed.stdout.strip()
    if completed.returncode != 0 or not commit:
        return None
    return commit


def _chunk_shape(value: tuple[int, int]) -> tuple[int, int]:
    if not isinstance(value, tuple) or len(value) != 2:
        raise ValueError("chunk_shape must be a two-item tuple.")
    _positive_int(value[0], "chunk_shape[0]")
    _positive_int(value[1], "chunk_shape[1]")
    return value


def _positive_int(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value!r}.")


def _nonnegative_int(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer, got {value!r}.")


def _positive_float(value: float, name: str) -> float:
    number = _finite_float(value, name)
    if number <= 0.0:
        raise ValueError(f"{name} must be positive, got {number!r}.")
    return number


def _finite_nonnegative_float(value: object, name: str) -> float:
    number = _finite_float(value, name)
    if number < 0.0:
        raise ValueError(f"{name} must be non-negative, got {number!r}.")
    return number


def _finite_float(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite, got {value!r}.")
    return number
