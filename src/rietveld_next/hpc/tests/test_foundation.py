"""Tests for HPC and cloud foundation payloads."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from rietveld_next.hpc import (
    BeamlineFrame,
    BeamlineLiveIngestMock,
    BenchmarkClusterSmokeFixture,
    DaskAdapter,
    JobResult,
    JobSpec,
    KubernetesWorkerManifest,
    ObjectStorageURI,
    ResultDatabaseWritePayload,
    RetryBackoffPolicy,
    SlurmJobArrayAdapter,
    build_status_stream,
    capture_hpc_provenance,
    collect_slurm_results,
)


class SlurmFoundationTests(unittest.TestCase):
    """Validate dry-run Slurm artifacts and local result collection."""

    def test_slurm_artifacts_are_deterministic(self) -> None:
        adapter = SlurmJobArrayAdapter(
            job_name="rn-smoke",
            result_uri=ObjectStorageURI.parse("file:///tmp/rietveld-next/results"),
            cpus_per_task=2,
        )
        jobs = [
            JobSpec("b", "refine", {"sample": "b"}, metadata={"beamline": "mock"}),
            JobSpec("a", "refine", {"sample": "a"}, resources={"cpus": 2}),
        ]

        artifacts = adapter.render_artifacts(jobs)
        manifest_lines = [json.loads(line) for line in artifacts.task_manifest_jsonl.splitlines()]

        self.assertIn("#SBATCH --array=0-1", artifacts.script_text)
        self.assertIn("#SBATCH --cpus-per-task=2", artifacts.script_text)
        self.assertEqual(artifacts.job_count, 2)
        self.assertEqual([line["array_index"] for line in manifest_lines], [0, 1])
        self.assertEqual([line["job_id"] for line in manifest_lines], ["b", "a"])

    def test_collect_slurm_results_sorts_local_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            result_dir = Path(temporary_directory)
            (result_dir / "002.json").write_text(
                json.dumps(JobResult("b", "refine", "ok", {"value": 2}).to_dict()),
                encoding="utf-8",
            )
            (result_dir / "001.json").write_text(
                json.dumps(JobResult("a", "refine", "error", error="failed").to_dict()),
                encoding="utf-8",
            )

            results = collect_slurm_results(result_dir)

        self.assertEqual([result.job_id for result in results], ["a", "b"])
        self.assertEqual(results[0].status, "error")
        self.assertEqual(results[1].output, {"value": 2})


class OptionalAdapterTests(unittest.TestCase):
    """Validate optional scheduler skip behavior."""

    def test_dask_adapter_reports_unavailable_and_skips(self) -> None:
        adapter = DaskAdapter(dependency_available=False)

        availability = adapter.availability()
        results = adapter.submit_many([JobSpec("job", "refine", {})])

        self.assertFalse(availability.available)
        self.assertEqual(availability.status, "unavailable")
        self.assertEqual(results[0].status, "skipped")
        self.assertIn("not installed", results[0].error or "")

    def test_skeleton_cancellation_is_unsupported(self) -> None:
        adapter = DaskAdapter(dependency_available=True)

        cancellation = adapter.cancel_job("job")

        self.assertFalse(cancellation.accepted)
        self.assertEqual(cancellation.status, "unsupported")


class CloudPayloadTests(unittest.TestCase):
    """Validate cloud and distributed result payload models."""

    def test_object_storage_uri_parse_and_round_trip(self) -> None:
        uri = ObjectStorageURI.parse("s3://bucket/path/to/result.json")

        self.assertEqual(uri.scheme, "s3")
        self.assertEqual(uri.bucket, "bucket")
        self.assertEqual(uri.key, "path/to/result.json")
        self.assertEqual(uri.to_uri(), "s3://bucket/path/to/result.json")

    def test_object_storage_uri_rejects_relative_file_uri(self) -> None:
        with self.assertRaisesRegex(ValueError, "absolute"):
            ObjectStorageURI.parse("file://relative/path")

    def test_result_database_writer_payload_validates_primary_key(self) -> None:
        payload = ResultDatabaseWritePayload(
            destination=ObjectStorageURI.parse("gs://bucket/results/table.json"),
            table="hpc_results",
            records=[{"job_id": "job", "status": "ok"}],
            metadata={"schema": "test"},
        )

        self.assertEqual(payload.to_dict()["records"], [{"job_id": "job", "status": "ok"}])
        self.assertEqual(payload.to_dict()["destination"]["scheme"], "gs")

    def test_result_database_writer_payload_rejects_missing_primary_key(self) -> None:
        with self.assertRaisesRegex(ValueError, "primary key"):
            ResultDatabaseWritePayload(
                destination=ObjectStorageURI.parse("az://container/results/table.json"),
                table="hpc_results",
                records=[{"status": "ok"}],
            )

    def test_kubernetes_manifest_payload_is_framework_free(self) -> None:
        manifest = KubernetesWorkerManifest(
            name="rn-worker",
            image="rietveld-next:test",
            command=["python", "-m", "rietveld_next.hpc.worker"],
            env={"RN_MODE": "dry-run"},
            labels={"batch": "smoke"},
            resources={"requests": {"cpu": "1"}},
        ).to_dict()

        container = manifest["spec"]["template"]["spec"]["containers"][0]
        self.assertEqual(manifest["kind"], "Job")
        self.assertEqual(container["env"], [{"name": "RN_MODE", "value": "dry-run"}])
        self.assertEqual(container["resources"], {"requests": {"cpu": "1"}})


class StreamRetryAndProvenanceTests(unittest.TestCase):
    """Validate stream records, retry policy, smoke fixtures, and provenance."""

    def test_smoke_fixture_generates_deterministic_jobs(self) -> None:
        fixture = BenchmarkClusterSmokeFixture(
            fixture_id="smoke",
            scheduler="local",
            job_count=2,
            payload_size=16,
            metadata={"dataset": "synthetic"},
        )

        jobs = fixture.to_jobs()

        self.assertEqual([job.job_id for job in jobs], ["smoke-0000", "smoke-0001"])
        self.assertEqual(jobs[0].metadata["dataset"], "synthetic")

    def test_beamline_live_ingest_mock_polls_in_sequence_order(self) -> None:
        source = ObjectStorageURI.parse("file:///tmp/beamline/frame.dat")
        frames = [
            BeamlineFrame("frame-2", 2, source, "sha256:def"),
            BeamlineFrame("frame-1", 1, source, "sha256:abc", metadata={"units": "counts"}),
        ]
        ingest = BeamlineLiveIngestMock(frames)

        first_batch = ingest.poll(limit=1)
        second_batch = ingest.poll()

        self.assertEqual([frame.frame_id for frame in first_batch], ["frame-1"])
        self.assertEqual([frame.frame_id for frame in second_batch], ["frame-2"])

    def test_status_stream_records_results(self) -> None:
        records = build_status_stream(
            [
                JobResult("a", "refine", "ok"),
                JobResult("b", "refine", "skipped", error="optional dependency missing"),
            ],
            start_sequence=5,
        )

        self.assertEqual([record.sequence for record in records], [5, 6])
        self.assertEqual(records[1].to_dict()["status"], "skipped")
        self.assertEqual(records[0].details["command"], "refine")

    def test_retry_backoff_policy_is_deterministic(self) -> None:
        policy = RetryBackoffPolicy(max_attempts=3, initial_delay_seconds=0.5, multiplier=3.0, max_delay_seconds=2.0)
        result = JobResult("job", "refine", "error", error="transient")

        self.assertTrue(policy.should_retry(result, attempt_index=0))
        self.assertFalse(policy.should_retry(result, attempt_index=2))
        self.assertEqual([policy.delay_for_attempt(index) for index in range(3)], [0.5, 1.5, 2.0])

    def test_hpc_provenance_captures_payload_digest_and_environment(self) -> None:
        jobs = [JobSpec("job", "refine", {"sample": "a"}, metadata={"source": "synthetic"})]
        results = [JobResult("job", "refine", "ok", {"rwp": 12.3})]

        provenance = capture_hpc_provenance(
            run_id="run-1",
            scheduler="local",
            jobs=jobs,
            results=results,
            environment={"python_version": "3.test"},
            assumptions=("dry-run local fixture",),
        ).to_dict()

        self.assertEqual(provenance["schema_version"], "hpc-provenance-v1")
        self.assertEqual(provenance["status_counts"], {"ok": 1})
        self.assertTrue(provenance["jobs"][0]["payload_digest"].startswith("sha256:"))
        self.assertEqual(provenance["environment"], {"python_version": "3.test"})

    def test_hpc_provenance_rejects_missing_result(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing job_id"):
            capture_hpc_provenance(
                run_id="run-1",
                scheduler="local",
                jobs=[JobSpec("job", "refine", {})],
                results=[],
            )


if __name__ == "__main__":
    unittest.main()
