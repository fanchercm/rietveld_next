"""Slurm job-array artifact generation and local result collection."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Sequence

from rietveld_next.hpc.object_store import ObjectStorageURI
from rietveld_next.hpc.scheduler import JobResult, JobSpec
from rietveld_next.hpc.serialization import stable_json


SLURM_ARRAY_SCHEMA_VERSION = "hpc-slurm-array-v1"


@dataclass(frozen=True)
class SlurmArrayArtifacts:
    """Generated Slurm job-array artifacts.

    Args:
        job_name: Slurm job name.
        script_text: Deterministic ``sbatch`` script content.
        task_manifest_jsonl: JSONL task manifest, one line per array index.
        result_uri: Base URI where array task results should be written.
    """

    job_name: str
    script_text: str
    task_manifest_jsonl: str
    result_uri: ObjectStorageURI
    schema_version: str = SLURM_ARRAY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.job_name:
            raise ValueError("SlurmArrayArtifacts.job_name must be non-empty")
        if not self.script_text:
            raise ValueError("SlurmArrayArtifacts.script_text must be non-empty")

    @property
    def job_count(self) -> int:
        """Number of array tasks in the manifest."""

        return len([line for line in self.task_manifest_jsonl.splitlines() if line])

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible artifact summary."""

        return {
            "schema_version": self.schema_version,
            "job_name": self.job_name,
            "job_count": self.job_count,
            "script_text": self.script_text,
            "task_manifest_jsonl": self.task_manifest_jsonl,
            "result_uri": self.result_uri.to_dict(),
        }


@dataclass(frozen=True)
class SlurmJobArrayAdapter:
    """Dry-run Slurm job-array adapter.

    The adapter only renders submission artifacts. It never calls ``sbatch`` and
    therefore remains safe for CI and machines without Slurm installed.
    """

    job_name: str
    result_uri: ObjectStorageURI
    partition: str | None = None
    time_limit: str = "00:05:00"
    cpus_per_task: int = 1

    def __post_init__(self) -> None:
        if not self.job_name:
            raise ValueError("SlurmJobArrayAdapter.job_name must be non-empty")
        if not self.time_limit:
            raise ValueError("time_limit must be non-empty")
        if self.cpus_per_task < 1:
            raise ValueError("cpus_per_task must be positive")

    def render_artifacts(self, jobs: Sequence[JobSpec]) -> SlurmArrayArtifacts:
        """Render deterministic Slurm array artifacts for jobs."""

        if not jobs:
            raise ValueError("jobs must be non-empty")
        lines = [_manifest_record(index, job) for index, job in enumerate(jobs)]
        manifest_jsonl = "\n".join(stable_json(record) for record in lines) + "\n"
        return SlurmArrayArtifacts(
            job_name=self.job_name,
            script_text=self._render_script(len(jobs)),
            task_manifest_jsonl=manifest_jsonl,
            result_uri=self.result_uri,
        )

    def _render_script(self, job_count: int) -> str:
        partition_line = "" if self.partition is None else f"#SBATCH --partition={self.partition}\n"
        return (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f"#SBATCH --job-name={self.job_name}\n"
            f"#SBATCH --array=0-{job_count - 1}\n"
            f"#SBATCH --time={self.time_limit}\n"
            f"#SBATCH --cpus-per-task={self.cpus_per_task}\n"
            f"{partition_line}"
            "\n"
            "echo \"Rietveld Next dry-run Slurm artifact for task ${SLURM_ARRAY_TASK_ID}\"\n"
            "echo \"Task payload is read from task_manifest.jsonl by array index.\"\n"
        )


def collect_slurm_results(directory: str | Path, *, pattern: str = "*.json") -> tuple[JobResult, ...]:
    """Collect locally written Slurm result JSON files in deterministic order.

    Args:
        directory: Local directory containing JSON result files.
        pattern: Glob pattern for result files.

    Returns:
        Results sorted by file name.

    Raises:
        FileNotFoundError: If directory does not exist.
        ValueError: If a result file is malformed.
    """

    result_dir = Path(directory)
    if not result_dir.exists():
        raise FileNotFoundError(f"Slurm result directory does not exist: {result_dir}")
    if not result_dir.is_dir():
        raise ValueError(f"Slurm result path is not a directory: {result_dir}")

    results: list[JobResult] = []
    for path in sorted(result_dir.glob(pattern), key=lambda item: item.name):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in Slurm result file {path.name}: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"Slurm result file {path.name} must contain a JSON object")
        try:
            results.append(
                JobResult(
                    job_id=data["job_id"],
                    command=data["command"],
                    status=data["status"],
                    output=data.get("output"),
                    error=data.get("error"),
                    provenance=data.get("provenance"),
                )
            )
        except KeyError as exc:
            raise ValueError(f"Slurm result file {path.name} is missing field {exc.args[0]!r}") from exc
    return tuple(results)


def _manifest_record(array_index: int, job: JobSpec) -> dict[str, Any]:
    return {
        "array_index": array_index,
        "job_id": job.job_id,
        "command": job.command,
        "payload": dict(sorted(job.payload.items())),
        "resources": dict(sorted(job.resources.items())),
        "metadata": dict(sorted(job.metadata.items())),
    }
