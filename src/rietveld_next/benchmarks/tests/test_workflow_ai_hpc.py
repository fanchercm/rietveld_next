"""Tests for workflow, AI, and HPC benchmark helpers."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from rietveld_next.benchmarks.results import validate_benchmark_result_dict
from rietveld_next.benchmarks.workflow_ai_hpc import (
    build_deterministic_tool_registry,
    run_ai_tool_call_overhead_benchmark,
    run_sequential_refinement_workflow_overhead_benchmark,
    run_slurm_job_array_packaging_benchmark,
)


class SequentialWorkflowBenchmarkTests(unittest.TestCase):
    """Validate deterministic sequential workflow benchmark records."""

    def test_sequential_benchmark_reports_trajectory_and_failures(self) -> None:
        result = run_sequential_refinement_workflow_overhead_benchmark(sequence_points=3, iterations=1)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.input_size, 3)
        self.assertEqual(result.environment["sequence_points"], 3)
        self.assertEqual(result.environment["failures"], 0)
        self.assertEqual(len(result.environment["parameter_trajectory"]), 3)
        self.assertEqual(result.environment["parameter_trajectory_checksum"], result.checksum)
        self.assertIn("median", result.environment["per_point_runtime_seconds"])
        validate_benchmark_result_dict(result.to_dict())

    def test_sequential_benchmark_rejects_invalid_sequence_points(self) -> None:
        with self.assertRaisesRegex(ValueError, "sequence_points must be a positive integer"):
            run_sequential_refinement_workflow_overhead_benchmark(sequence_points=0)


class AiToolCallBenchmarkTests(unittest.TestCase):
    """Validate deterministic AI tool-call overhead benchmark records."""

    def test_mock_tool_registry_fixture_excludes_llm_calls(self) -> None:
        registry = build_deterministic_tool_registry()

        result = registry.call_tool("estimate_background", {"scan_id": "scan", "point_count": 64})

        self.assertEqual(result.status, "ok")
        self.assertEqual(len(registry.contract_schema()), 3)
        self.assertEqual(len(registry.action_log), 1)

    def test_ai_tool_call_benchmark_reports_latency_and_orchestration(self) -> None:
        result = run_ai_tool_call_overhead_benchmark(tool_calls=6)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.iterations, 6)
        self.assertFalse(result.environment["llm_latency_included"])
        self.assertGreater(result.environment["calls_per_second"], 0.0)
        self.assertGreaterEqual(result.environment["orchestration_runtime_seconds"], 0.0)
        self.assertEqual(result.environment["numerical_runtime_seconds"], 0.0)
        self.assertEqual(result.environment["action_log_entries"], 6)
        self.assertEqual(result.environment["per_tool_latency_seconds"]["estimate_background"]["calls"], 2)
        validate_benchmark_result_dict(result.to_dict())

    def test_ai_tool_call_benchmark_rejects_invalid_call_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "tool_calls must be a positive integer"):
            run_ai_tool_call_overhead_benchmark(tool_calls=0)


class SlurmPackagingBenchmarkTests(unittest.TestCase):
    """Validate dry-run Slurm packaging benchmark records."""

    def test_slurm_packaging_writes_requested_artifacts_without_submission(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            result = run_slurm_job_array_packaging_benchmark(output_directory=output_directory, job_count=2)

            script_path = output_directory / "submit_array.sbatch"
            manifest_path = output_directory / "task_manifest.jsonl"

            self.assertTrue(script_path.exists())
            self.assertTrue(manifest_path.exists())
            self.assertIn("#SBATCH --array=0-1", script_path.read_text(encoding="utf-8"))
            self.assertEqual(len(manifest_path.read_text(encoding="utf-8").splitlines()), 2)
            self.assertFalse(result.environment["submitted_jobs"])
            self.assertEqual(result.environment["job_count"], 2)
            self.assertEqual(len(result.environment["generated_files"]), 2)
            self.assertGreater(result.environment["payload_size_bytes"], 0)
            validate_benchmark_result_dict(result.to_dict())

    def test_slurm_packaging_rejects_invalid_job_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(ValueError, "job_count must be a positive integer"):
                run_slurm_job_array_packaging_benchmark(output_directory=temporary_directory, job_count=0)

    def test_slurm_packaging_rejects_empty_output_directory(self) -> None:
        with self.assertRaisesRegex(ValueError, "output_directory must be a non-empty path"):
            run_slurm_job_array_packaging_benchmark(output_directory="")


if __name__ == "__main__":
    unittest.main()
