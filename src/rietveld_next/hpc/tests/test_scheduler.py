"""Tests for scheduler abstractions."""

from __future__ import annotations

import unittest

from rietveld_next.hpc import JobSpec, LocalParallelBatchRunner, LocalScheduler, summarize_results


class LocalSchedulerTests(unittest.TestCase):
    """Validate local scheduler behavior."""

    def test_submit_many_executes_in_order(self) -> None:
        scheduler = LocalScheduler({"echo": lambda payload: {"value": payload["value"]}})
        jobs = [
            JobSpec("a", "echo", {"value": 1}),
            JobSpec("b", "echo", {"value": 2}),
        ]

        results = scheduler.submit_many(jobs)

        self.assertEqual([result.job_id for result in results], ["a", "b"])
        self.assertEqual(results[1].output, {"value": 2})

    def test_duplicate_job_ids_raise(self) -> None:
        scheduler = LocalScheduler({"echo": lambda payload: payload})

        with self.assertRaisesRegex(ValueError, "Duplicate job_id"):
            scheduler.submit_many(
                [
                    JobSpec("same", "echo", {}),
                    JobSpec("same", "echo", {}),
                ]
            )

    def test_unknown_command_records_error(self) -> None:
        scheduler = LocalScheduler({})

        results = scheduler.submit_many([JobSpec("job", "missing", {})])

        self.assertEqual(results[0].status, "error")
        self.assertIn("No local scheduler handler", results[0].error or "")

    def test_summarize_results_counts_statuses(self) -> None:
        scheduler = LocalScheduler({"ok": lambda payload: payload})
        results = scheduler.submit_many(
            [
                JobSpec("good", "ok", {}),
                JobSpec("bad", "missing", {}),
            ]
        )

        self.assertEqual(summarize_results(results), {"ok": 1, "error": 1})

    def test_job_spec_preserves_resources_and_metadata(self) -> None:
        job = JobSpec(
            "job",
            "echo",
            {"value": 1},
            resources={"cpus": 2},
            metadata={"sample_id": "s1"},
        )

        self.assertEqual(job.to_dict()["resources"], {"cpus": 2})
        self.assertEqual(job.to_dict()["metadata"], {"sample_id": "s1"})

    def test_cancelled_job_records_cancelled_result(self) -> None:
        scheduler = LocalScheduler({"echo": lambda payload: payload})

        cancellation = scheduler.cancel_job("job", reason="stale input")
        results = scheduler.submit_many([JobSpec("job", "echo", {"value": 1})])

        self.assertTrue(cancellation.accepted)
        self.assertEqual(results[0].status, "cancelled")
        self.assertEqual(results[0].error, "stale input")


class LocalParallelBatchRunnerTests(unittest.TestCase):
    """Validate deterministic local parallel batch execution."""

    def test_parallel_runner_returns_results_in_input_order(self) -> None:
        runner = LocalParallelBatchRunner(
            {"square": lambda payload: {"square": payload["value"] * payload["value"]}},
            max_workers=2,
        )
        jobs = [
            JobSpec("a", "square", {"value": 3}),
            JobSpec("b", "square", {"value": 2}),
            JobSpec("c", "square", {"value": 1}),
        ]

        batch = runner.run(jobs)

        self.assertTrue(batch.succeeded)
        self.assertEqual([result.job_id for result in batch.results], ["a", "b", "c"])
        self.assertEqual([result.output for result in batch.results], [{"square": 9}, {"square": 4}, {"square": 1}])

    def test_parallel_runner_rejects_invalid_worker_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "max_workers"):
            LocalParallelBatchRunner({}, max_workers=0)


if __name__ == "__main__":
    unittest.main()
