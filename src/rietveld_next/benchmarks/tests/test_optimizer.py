"""Tests for optimizer benchmark hooks."""

from __future__ import annotations

import unittest

from unittest.mock import patch

from rietveld_next.benchmarks import (
    run_automatic_differentiation_benchmark,
    run_global_multistart_benchmark,
    run_local_optimizer_benchmark,
    run_optimizer_scaling_benchmark,
    run_sparse_jacobian_assembly_benchmark,
)


class OptimizerBenchmarkTests(unittest.TestCase):
    """Smoke tests for opt-in optimizer benchmark records."""

    def test_local_optimizer_benchmark_reports_convergence_metrics(self) -> None:
        result = run_local_optimizer_benchmark(dimensions=2)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.name, "local_optimizer_quadratic")
        self.assertTrue(result.environment["converged"])
        self.assertEqual(result.environment["status"], "converged")
        self.assertEqual(result.environment["failure_status"], "invalid_initial_model")
        self.assertTrue(result.environment["unbounded_converged"])
        self.assertIn("final_objective", result.environment)
        self.assertIn("function_evaluations", result.environment)

    def test_local_optimizer_benchmark_keeps_generated_target_feasible(self) -> None:
        result = run_local_optimizer_benchmark(dimensions=11)

        self.assertTrue(result.environment["converged"])
        self.assertLess(result.environment["max_abs_parameter_error"], 1.0e-5)

    def test_local_optimizer_benchmark_rejects_invalid_dimension(self) -> None:
        with self.assertRaisesRegex(ValueError, "dimensions must be a positive integer"):
            run_local_optimizer_benchmark(dimensions=0)

    def test_sparse_jacobian_assembly_benchmark_reports_nonzeros(self) -> None:
        result = run_sparse_jacobian_assembly_benchmark(dimensions=3)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.environment["nonzero_count"], 3)
        self.assertAlmostEqual(result.environment["density"], 1.0 / 3.0, places=15)
        self.assertTrue(result.environment["reference_matches_dense_fixture"])
        self.assertEqual(result.environment["reference_max_abs_error"], 0.0)
        self.assertEqual(result.checksum, 6.0)

    def test_automatic_differentiation_benchmark_skips_when_jax_unavailable(self) -> None:
        real_import = __import__

        def blocked_import(name: str, *args: object, **kwargs: object) -> object:
            if name == "jax" or name.startswith("jax."):
                raise ImportError("blocked in test")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=blocked_import):
            result = run_automatic_differentiation_benchmark(dimensions=3)

        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.backend, "jax")
        self.assertEqual(result.environment["derivative_backend"], "jax_jacfwd")
        self.assertIn("JAX", result.skip_reason or "")

    def test_optimizer_scaling_benchmark_reports_evaluations(self) -> None:
        result = run_optimizer_scaling_benchmark(max_dimensions=2)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.iterations, 2)
        self.assertIn("1", result.environment["evaluations_by_dimension"])
        self.assertIn("2", result.environment["evaluations_by_dimension"])
        self.assertEqual(result.environment["status_by_dimension"]["1"], "converged")
        self.assertLess(result.environment["max_abs_parameter_error_by_dimension"]["2"], 1.0e-5)

    def test_global_multistart_benchmark_reports_best_result(self) -> None:
        result = run_global_multistart_benchmark(dimensions=2, start_count=3)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.environment["status"], "completed")
        self.assertTrue(result.environment["best_converged"])
        self.assertIn("total_function_evaluations", result.environment)
        self.assertIn("candidate_statuses", result.environment)
        self.assertGreater(result.environment["success_rate"], 0.0)
        self.assertLess(result.environment["max_abs_parameter_error"], 1.0e-5)


if __name__ == "__main__":
    unittest.main()
