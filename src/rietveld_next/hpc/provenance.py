"""HPC provenance capture for scheduler runs."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import platform
import sys
from typing import Any, Mapping, Sequence

from rietveld_next.hpc.scheduler import JobResult, JobSpec, summarize_results
from rietveld_next.hpc.serialization import immutable_mapping, stable_json


HPC_PROVENANCE_SCHEMA_VERSION = "hpc-provenance-v1"


@dataclass(frozen=True)
class JobProvenanceRecord:
    """Provenance for one scheduled job."""

    job_id: str
    command: str
    status: str
    payload_digest: str
    resources: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.job_id:
            raise ValueError("job_id must be non-empty")
        if not self.command:
            raise ValueError("command must be non-empty")
        if not self.payload_digest:
            raise ValueError("payload_digest must be non-empty")
        object.__setattr__(self, "resources", immutable_mapping(self.resources, "resources"))
        object.__setattr__(self, "metadata", immutable_mapping(self.metadata, "metadata"))

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible job provenance mapping."""

        return {
            "job_id": self.job_id,
            "command": self.command,
            "status": self.status,
            "payload_digest": self.payload_digest,
            "resources": dict(sorted(self.resources.items())),
            "metadata": dict(sorted(self.metadata.items())),
            "error": self.error,
        }


@dataclass(frozen=True)
class HPCProvenanceRecord:
    """Versioned HPC run provenance record."""

    run_id: str
    scheduler: str
    captured_at_utc: str
    jobs: tuple[JobProvenanceRecord, ...]
    environment: Mapping[str, Any] = field(default_factory=dict)
    assumptions: tuple[str, ...] = ()
    schema_version: str = field(default=HPC_PROVENANCE_SCHEMA_VERSION, init=False)

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
        if not self.scheduler:
            raise ValueError("scheduler must be non-empty")
        if not self.captured_at_utc:
            raise ValueError("captured_at_utc must be non-empty")
        object.__setattr__(self, "jobs", tuple(self.jobs))
        object.__setattr__(self, "environment", immutable_mapping(self.environment, "environment"))
        object.__setattr__(self, "assumptions", tuple(self.assumptions))
        if any(not assumption for assumption in self.assumptions):
            raise ValueError("assumptions must not contain empty strings")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible provenance mapping."""

        status_counts: dict[str, int] = {}
        for job in self.jobs:
            status_counts[job.status] = status_counts.get(job.status, 0) + 1
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "scheduler": self.scheduler,
            "captured_at_utc": self.captured_at_utc,
            "environment": dict(sorted(self.environment.items())),
            "assumptions": list(self.assumptions),
            "status_counts": dict(sorted(status_counts.items())),
            "jobs": [job.to_dict() for job in self.jobs],
        }


def capture_runtime_environment() -> dict[str, str]:
    """Capture lightweight runtime environment metadata."""

    return {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "implementation": platform.python_implementation(),
    }


def capture_hpc_provenance(
    *,
    run_id: str,
    scheduler: str,
    jobs: Sequence[JobSpec],
    results: Sequence[JobResult],
    captured_at_utc: str = "not-recorded",
    environment: Mapping[str, Any] | None = None,
    assumptions: Sequence[str] = (),
) -> HPCProvenanceRecord:
    """Capture deterministic provenance for scheduler jobs and results.

    Args:
        run_id: Stable run identifier.
        scheduler: Scheduler or adapter name.
        jobs: Submitted jobs.
        results: Scheduler results.
        captured_at_utc: Explicit timestamp or ``"not-recorded"`` for dry-run
            records that should remain deterministic in tests.
        environment: Optional runtime environment metadata.
        assumptions: Explicit scheduler or dry-run assumptions.

    Returns:
        Versioned HPC provenance record.

    Raises:
        ValueError: If job/result identifiers do not align.
    """

    results_by_id = {result.job_id: result for result in results}
    if len(results_by_id) != len(results):
        raise ValueError("results must not contain duplicate job_id values")
    missing = [job.job_id for job in jobs if job.job_id not in results_by_id]
    if missing:
        raise ValueError(f"results are missing job_id values: {missing}")
    summarize_results(results)

    job_records = []
    for job in jobs:
        result = results_by_id[job.job_id]
        job_records.append(
            JobProvenanceRecord(
                job_id=job.job_id,
                command=job.command,
                status=result.status,
                payload_digest=_payload_digest(job.payload),
                resources=job.resources,
                metadata=job.metadata,
                error=result.error,
            )
        )
    return HPCProvenanceRecord(
        run_id=run_id,
        scheduler=scheduler,
        captured_at_utc=captured_at_utc,
        jobs=tuple(job_records),
        environment={} if environment is None else environment,
        assumptions=tuple(assumptions),
    )


def _payload_digest(payload: Mapping[str, Any]) -> str:
    encoded = stable_json(dict(payload)).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
