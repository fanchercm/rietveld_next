"""Benchmark cluster smoke-test fixture model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from rietveld_next.hpc.scheduler import JobSpec
from rietveld_next.hpc.serialization import immutable_mapping


SMOKE_FIXTURE_SCHEMA_VERSION = "hpc-cluster-smoke-fixture-v1"


@dataclass(frozen=True)
class BenchmarkClusterSmokeFixture:
    """Small synthetic fixture for scheduler smoke tests.

    Args:
        fixture_id: Stable fixture identifier.
        scheduler: Intended scheduler or adapter name.
        job_count: Number of synthetic jobs to create.
        payload_size: Synthetic payload size hint in arbitrary units.
        command: Logical command assigned to generated jobs.
        metadata: Additional fixture metadata.
    """

    fixture_id: str
    scheduler: str
    job_count: int
    payload_size: int
    command: str = "hpc.smoke"
    metadata: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = field(default=SMOKE_FIXTURE_SCHEMA_VERSION, init=False)

    def __post_init__(self) -> None:
        if not self.fixture_id:
            raise ValueError("fixture_id must be non-empty")
        if not self.scheduler:
            raise ValueError("scheduler must be non-empty")
        if not self.command:
            raise ValueError("command must be non-empty")
        if isinstance(self.job_count, bool) or self.job_count < 1:
            raise ValueError("job_count must be a positive integer")
        if isinstance(self.payload_size, bool) or self.payload_size < 0:
            raise ValueError("payload_size must be non-negative")
        object.__setattr__(self, "metadata", immutable_mapping(self.metadata, "metadata"))

    def to_jobs(self) -> tuple[JobSpec, ...]:
        """Create deterministic synthetic scheduler jobs."""

        return tuple(
            JobSpec(
                job_id=f"{self.fixture_id}-{index:04d}",
                command=self.command,
                payload={"index": index, "payload_size": self.payload_size},
                metadata={"fixture_id": self.fixture_id, **dict(self.metadata)},
            )
            for index in range(self.job_count)
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible fixture mapping."""

        return {
            "schema_version": self.schema_version,
            "fixture_id": self.fixture_id,
            "scheduler": self.scheduler,
            "job_count": self.job_count,
            "payload_size": self.payload_size,
            "command": self.command,
            "metadata": dict(sorted(self.metadata.items())),
        }
