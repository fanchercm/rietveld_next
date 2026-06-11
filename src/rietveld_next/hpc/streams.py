"""Deterministic ingest and status stream records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from rietveld_next.hpc.object_store import ObjectStorageURI
from rietveld_next.hpc.scheduler import JobResult, SUPPORTED_JOB_STATUSES
from rietveld_next.hpc.serialization import immutable_mapping


STATUS_STREAM_SCHEMA_VERSION = "hpc-status-stream-v1"
BEAMLINE_FRAME_SCHEMA_VERSION = "hpc-beamline-frame-v1"


@dataclass(frozen=True)
class StatusStreamRecord:
    """A logical real-time status update record.

    Args:
        sequence: Monotonic stream sequence number.
        job_id: Stable job identifier.
        status: Scheduler status.
        message: Human-readable update.
        logical_time: Deterministic logical timestamp in ticks.
        details: Optional JSON-like metadata.
    """

    sequence: int
    job_id: str
    status: str
    message: str
    logical_time: int
    details: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = field(default=STATUS_STREAM_SCHEMA_VERSION, init=False)

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")
        if self.logical_time < 0:
            raise ValueError("logical_time must be non-negative")
        if not self.job_id:
            raise ValueError("job_id must be non-empty")
        if self.status not in SUPPORTED_JOB_STATUSES:
            raise ValueError("status is not supported")
        if not self.message:
            raise ValueError("message must be non-empty")
        object.__setattr__(self, "details", immutable_mapping(self.details, "details"))

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible stream record."""

        return {
            "schema_version": self.schema_version,
            "sequence": self.sequence,
            "job_id": self.job_id,
            "status": self.status,
            "message": self.message,
            "logical_time": self.logical_time,
            "details": dict(sorted(self.details.items())),
        }


def build_status_stream(results: Sequence[JobResult], *, start_sequence: int = 0) -> tuple[StatusStreamRecord, ...]:
    """Build status-stream records from scheduler results."""

    if start_sequence < 0:
        raise ValueError("start_sequence must be non-negative")
    records: list[StatusStreamRecord] = []
    for offset, result in enumerate(results):
        sequence = start_sequence + offset
        records.append(
            StatusStreamRecord(
                sequence=sequence,
                job_id=result.job_id,
                status=result.status,
                message=f"{result.job_id} {result.status}",
                logical_time=sequence,
                details={"command": result.command},
            )
        )
    return tuple(records)


@dataclass(frozen=True)
class BeamlineFrame:
    """Synthetic beamline ingest frame.

    Args:
        frame_id: Stable frame identifier.
        sequence: Monotonic frame sequence.
        source_uri: Object URI for the source data.
        checksum: Deterministic checksum for the source payload.
        metadata: Frame metadata such as detector, exposure, or units.
    """

    frame_id: str
    sequence: int
    source_uri: ObjectStorageURI
    checksum: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = field(default=BEAMLINE_FRAME_SCHEMA_VERSION, init=False)

    def __post_init__(self) -> None:
        if not self.frame_id:
            raise ValueError("frame_id must be non-empty")
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")
        if not self.checksum:
            raise ValueError("checksum must be non-empty")
        object.__setattr__(self, "metadata", immutable_mapping(self.metadata, "metadata"))

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible frame mapping."""

        return {
            "schema_version": self.schema_version,
            "frame_id": self.frame_id,
            "sequence": self.sequence,
            "source_uri": self.source_uri.to_dict(),
            "checksum": self.checksum,
            "metadata": dict(sorted(self.metadata.items())),
        }


class BeamlineLiveIngestMock:
    """Deterministic live-ingest mock for beamline frames."""

    def __init__(self, frames: Sequence[BeamlineFrame]) -> None:
        sequences = [frame.sequence for frame in frames]
        if len(sequences) != len(set(sequences)):
            raise ValueError("Beamline frame sequences must be unique")
        self._frames = tuple(sorted(frames, key=lambda frame: frame.sequence))
        self._cursor = 0

    def poll(self, *, limit: int | None = None) -> tuple[BeamlineFrame, ...]:
        """Return the next frames in sequence order."""

        if limit is not None and limit < 1:
            raise ValueError("limit must be positive when provided")
        end = len(self._frames) if limit is None else min(len(self._frames), self._cursor + limit)
        batch = self._frames[self._cursor : end]
        self._cursor = end
        return batch

    def reset(self) -> None:
        """Reset the mock stream cursor to the first frame."""

        self._cursor = 0
