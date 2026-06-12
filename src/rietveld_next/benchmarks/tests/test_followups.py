"""Tests for deterministic benchmark follow-up helpers."""

from __future__ import annotations

import unittest

from rietveld_next.benchmarks.followups import (
    benchmark_documentation_hub_payload,
    compare_benchmark_regression_baseline,
    parquet_result_table_io_skipped_benchmark,
    run_agent_replay_provenance_validation_benchmark,
    run_batch_throughput_benchmark,
    run_benchmark_documentation_hub_payload_benchmark,
    run_benchmark_regression_baseline_comparison,
    run_covariance_correlation_computation_benchmark,
    run_edxrd_calibration_workflow_benchmark,
    run_parametric_refinement_benchmark,
    run_tof_calibration_refinement_benchmark,
    rust_gaussian_profile_skipped_benchmark,
    validate_agent_action_log,
    zarr_profile_array_io_skipped_benchmark,
)
from rietveld_next.benchmarks.results import validate_benchmark_result_dict
from rietveld_next.workflows.replay import WorkflowAction


class OptionalBackendSkippedRecordTests(unittest.TestCase):
    """Validate skipped follow-up records for non-default backends."""

    def test_rust_gaussian_skipped_record_reports_contract(self) -> None:
        result = rust_gaussian_profile_skipped_benchmark(input_size=32, peak_count=2)

        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.backend, "rust")
        self.assertIn("Rust Gaussian", result.skip_reason or "")
        self.assertEqual(result.environment["peak_count"], 2)
        self.assertFalse(result.environment["live_optional_backend"])
        self.assertEqual(result.environment["kernel_contract"]["dtype"], "f64")
        validate_benchmark_result_dict(result.to_dict())

    def test_storage_optional_backend_records_do_not_import_live_backends(self) -> None:
        zarr = zarr_profile_array_io_skipped_benchmark(profile_count=2, point_count=8, chunk_shape=(1, 8))
        parquet = parquet_result_table_io_skipped_benchmark(row_count=3, column_count=4)

        self.assertEqual(zarr.status, "skipped")
        self.assertEqual(zarr.environment["chunk_shape"], [1, 8])
        self.assertIsNone(zarr.environment["write_runtime_seconds"])
        self.assertEqual(parquet.status, "skipped")
        self.assertEqual(parquet.environment["row_count"], 3)
        self.assertEqual(len(parquet.environment["schema_columns"]), 4)
        validate_benchmark_result_dict(zarr.to_dict())
        validate_benchmark_result_dict(parquet.to_dict())

    def test_zarr_chunk_shape_validation(self) -> None:
        with self.assertRaisesRegex(ValueError, "chunk_shape"):
            zarr_profile_array_io_skipped_benchmark(chunk_shape=(0, 8))


class WorkflowFollowupBenchmarkTests(unittest.TestCase):
    """Validate workflow benchmark follow-up smoke records."""

    def test_parametric_refinement_reports_function_error_and_baseline(self) -> None:
        result = run_parametric_refinement_benchmark(point_count=6)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.input_size, 6)
        self.assertEqual(result.environment["function_model"]["parameter"], "lattice_a_angstrom")
        self.assertIn("temperature_k", result.environment["external_variables"])
        self.assertLess(result.environment["parameter_function_error"]["rms_error"], 3.0e-5)
        self.assertIn("sequential_baseline_error", result.environment)
        validate_benchmark_result_dict(result.to_dict())

    def test_parametric_refinement_requires_two_points(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 2"):
            run_parametric_refinement_benchmark(point_count=1)

    def test_batch_throughput_reports_worker_count_and_successes(self) -> None:
        result = run_batch_throughput_benchmark(job_count=4, worker_count=2)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.environment["job_count"], 4)
        self.assertEqual(result.environment["worker_count"], 2)
        self.assertEqual(result.environment["success_count"], 4)
        self.assertEqual(result.environment["failure_count"], 0)
        self.assertGreater(result.environment["refinements_per_second"], 0.0)
        validate_benchmark_result_dict(result.to_dict())

    def test_batch_throughput_rejects_invalid_workers(self) -> None:
        with self.assertRaisesRegex(ValueError, "worker_count"):
            run_batch_throughput_benchmark(worker_count=0)


class CalibrationFollowupBenchmarkTests(unittest.TestCase):
    """Validate TOF and EDXRD calibration benchmark smoke records."""

    def test_tof_calibration_recovers_parameters_by_bank(self) -> None:
        result = run_tof_calibration_refinement_benchmark(bank_count=2, peak_count=4)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.environment["convergence_status"], "ok")
        self.assertEqual(len(result.environment["parameter_errors_by_bank"]), 2)
        self.assertLess(result.environment["max_abs_parameter_error"], 1.0e-8)
        self.assertEqual(result.environment["axis_units"]["tof"], "microsecond")
        validate_benchmark_result_dict(result.to_dict())

    def test_tof_calibration_requires_enough_peaks(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 3"):
            run_tof_calibration_refinement_benchmark(peak_count=2)

    def test_edxrd_calibration_reports_polynomial_and_standard_peaks(self) -> None:
        result = run_edxrd_calibration_workflow_benchmark(peak_count=5)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.environment["polynomial_order"], 2)
        self.assertEqual(len(result.environment["standard_peaks"]), 5)
        self.assertLess(result.environment["max_abs_coefficient_error"], 1.0e-10)
        validate_benchmark_result_dict(result.to_dict())

    def test_edxrd_calibration_rejects_unsupported_order(self) -> None:
        with self.assertRaisesRegex(ValueError, "polynomial_order"):
            run_edxrd_calibration_workflow_benchmark(polynomial_order=1)


class DiagnosticsAndAiFollowupBenchmarkTests(unittest.TestCase):
    """Validate diagnostics and AI replay follow-up records."""

    def test_covariance_correlation_reports_structured_singular_case(self) -> None:
        result = run_covariance_correlation_computation_benchmark(parameter_count=3)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.environment["matrix_dimensions"], [3, 3])
        self.assertEqual(result.environment["covariance_status"], "ok")
        self.assertEqual(result.environment["correlation_status"], "ok")
        self.assertTrue(result.environment["diagonal_positive"])
        self.assertEqual(result.environment["singular_case_status"], "singular")
        validate_benchmark_result_dict(result.to_dict())

    def test_agent_replay_reports_valid_and_invalid_logs(self) -> None:
        result = run_agent_replay_provenance_validation_benchmark(action_count=3)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.environment["actions_replayed"], 3)
        self.assertEqual(result.environment["replay_success_count"], 3)
        self.assertEqual(result.environment["validation_status"], "ok")
        self.assertEqual(result.environment["invalid_log_status"], "error")
        self.assertEqual(result.environment["invalid_log_errors"][0]["code"], "missing_provenance")
        validate_benchmark_result_dict(result.to_dict())

    def test_validate_agent_action_log_reports_structured_errors(self) -> None:
        action = WorkflowAction(
            sequence=0,
            step_id="s0",
            tool="record_observation",
            inputs={},
            status="ok",
            output={"accepted": True},
        )

        report = validate_agent_action_log((action,))

        self.assertEqual(report["status"], "error")
        self.assertEqual(report["errors"][0]["code"], "missing_provenance")


class InfrastructureFollowupBenchmarkTests(unittest.TestCase):
    """Validate regression baseline and documentation hub helpers."""

    def test_baseline_comparison_warns_by_default(self) -> None:
        current = {
            "name": "bench",
            "timing": {"median_seconds": 0.12},
        }
        baseline = {
            "name": "bench",
            "timing": {"median_seconds": 0.10},
        }

        report = compare_benchmark_regression_baseline(
            [current],
            [baseline],
            threshold_percent=10.0,
        )

        self.assertEqual(report["status"], "warn")
        self.assertFalse(report["fail_on_regression"])
        self.assertEqual(report["regression_count"], 1)
        self.assertEqual(report["comparisons"][0]["status"], "regression")

    def test_baseline_comparison_can_fail_explicitly(self) -> None:
        current = {"name": "bench", "timing": {"median_seconds": 0.12}}
        baseline = {"name": "bench", "timing": {"median_seconds": 0.10}}

        report = compare_benchmark_regression_baseline(
            [current],
            [baseline],
            threshold_percent=10.0,
            fail_on_regression=True,
        )

        self.assertEqual(report["status"], "fail")

    def test_baseline_comparison_smoke_record_is_valid(self) -> None:
        result = run_benchmark_regression_baseline_comparison()

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.environment["comparison_report"]["status"], "ok")
        self.assertEqual(result.environment["default_behavior"], "warn")
        validate_benchmark_result_dict(result.to_dict())

    def test_documentation_hub_payload_contains_required_sections(self) -> None:
        payload = benchmark_documentation_hub_payload()

        self.assertIn("quick", payload["commands"])
        self.assertIn("medium", payload["commands"])
        self.assertIn("large_opt_in", payload["commands"])
        self.assertIn("JAX compile time versus steady-state timing", payload["sections"])
        self.assertIn("Rust serial and parallel variants", payload["sections"])
        self.assertEqual(payload["ci_policy"]["default"], "smoke_only")

    def test_documentation_hub_payload_smoke_record_is_valid(self) -> None:
        result = run_benchmark_documentation_hub_payload_benchmark()

        self.assertEqual(result.status, "ok")
        self.assertIn("documentation_payload", result.environment)
        validate_benchmark_result_dict(result.to_dict())


if __name__ == "__main__":
    unittest.main()
