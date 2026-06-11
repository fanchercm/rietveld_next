"""Tests for scheduler abstractions."""

from __future__ import annotations

import unittest

from rietveld_next.hpc import JobSpec, LocalScheduler, summarize_results


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


if __name__ == "__main__":
    unittest.main()
