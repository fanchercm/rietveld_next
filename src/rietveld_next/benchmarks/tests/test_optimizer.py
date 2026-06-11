"""Tests for optimizer benchmark hooks."""

from __future__ import annotations

import unittest

from rietveld_next.benchmarks import run_local_optimizer_benchmark


class OptimizerBenchmarkTests(unittest.TestCase):
    """Smoke tests for opt-in optimizer benchmark records."""

    def test_local_optimizer_benchmark_reports_convergence_metrics(self) -> None:
        result = run_local_optimizer_benchmark(dimensions=2)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.name, "local_optimizer_quadratic")
        self.assertTrue(result.environment["converged"])
        self.assertEqual(result.environment["status"], "converged")
        self.assertIn("final_objective", result.environment)
        self.assertIn("function_evaluations", result.environment)

    def test_local_optimizer_benchmark_keeps_generated_target_feasible(self) -> None:
        result = run_local_optimizer_benchmark(dimensions=11)

        self.assertTrue(result.environment["converged"])
        self.assertLess(result.environment["max_abs_parameter_error"], 1.0e-5)

    def test_local_optimizer_benchmark_rejects_invalid_dimension(self) -> None:
        with self.assertRaisesRegex(ValueError, "dimensions must be a positive integer"):
            run_local_optimizer_benchmark(dimensions=0)


if __name__ == "__main__":
    unittest.main()
