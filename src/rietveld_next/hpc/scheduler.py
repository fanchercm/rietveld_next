"""Scheduler abstraction and deterministic local batch execution."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol, Sequence


JobHandler = Callable[[Mapping[str, Any]], Mapping[str, Any]]
SUPPORTED_JOB_STATUSES = frozenset({"queued", "running", "ok", "error", "cancelled", "skipped"})


@dataclass(frozen=True)
class JobSpec:
    """Scheduler-independent job request.

    Args:
        job_id: Stable identifier unique within a batch.
        command: Logical command name resolved by a scheduler adapter.
        payload: JSON-like command payload.
        resources: Requested scheduler resources, such as CPU or memory.
        metadata: User or workflow metadata carried into provenance records.

    Raises:
        ValueError: If identifiers are empty.
        TypeError: If mapping fields are not mappings.
    """

    job_id: str
    command: str
    payload: Mapping[str, Any]
    resources: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.job_id:
            raise ValueError("JobSpec.job_id must be non-empty")
        if not self.command:
            raise ValueError("JobSpec.command must be non-empty")
        if not isinstance(self.payload, Mapping):
            raise TypeError("JobSpec.payload must be a mapping")
        if not isinstance(self.resources, Mapping):
            raise TypeError("JobSpec.resources must be a mapping")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("JobSpec.metadata must be a mapping")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))
        object.__setattr__(self, "resources", MappingProxyType(dict(self.resources)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible job mapping."""

        return {
            "job_id": self.job_id,
            "command": self.command,
            "payload": dict(sorted(self.payload.items())),
            "resources": dict(sorted(self.resources.items())),
            "metadata": dict(sorted(self.metadata.items())),
        }


@dataclass(frozen=True)
class JobResult:
    """Result from a scheduler job.

    Args:
        job_id: Stable job identifier.
        command: Logical command name from the originating job.
        status: Scheduler status. Supported statuses are listed in
            :data:`SUPPORTED_JOB_STATUSES`.
        output: Optional JSON-like result payload.
        error: Optional human-readable failure, cancellation, or skip reason.
        provenance: Optional scheduler-specific provenance metadata.

    Raises:
        ValueError: If status or required identifiers are invalid.
        TypeError: If mapping fields are not mappings.
    """

    job_id: str
    command: str
    status: str
    output: Mapping[str, Any] | None = None
    error: str | None = None
    provenance: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.job_id:
            raise ValueError("JobResult.job_id must be non-empty")
        if not self.command:
            raise ValueError("JobResult.command must be non-empty")
        if self.status not in SUPPORTED_JOB_STATUSES:
            raise ValueError("JobResult.status is not a supported scheduler status")
        if self.output is not None:
            if not isinstance(self.output, Mapping):
                raise TypeError("JobResult.output must be a mapping or None")
            object.__setattr__(self, "output", MappingProxyType(dict(self.output)))
        if self.provenance is not None:
            if not isinstance(self.provenance, Mapping):
                raise TypeError("JobResult.provenance must be a mapping or None")
            object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible result mapping."""

        return {
            "job_id": self.job_id,
            "command": self.command,
            "status": self.status,
            "output": None if self.output is None else dict(sorted(self.output.items())),
            "error": self.error,
            "provenance": None if self.provenance is None else dict(sorted(self.provenance.items())),
        }


class Scheduler(Protocol):
    """Minimal scheduler interface shared by local and external adapters."""

    def submit_many(self, jobs: Sequence[JobSpec]) -> tuple[JobResult, ...]:
        """Submit or execute jobs and return one result per input job."""

    def cancel_job(self, job_id: str, *, reason: str = "cancelled by user") -> "CancellationResult":
        """Request cancellation for a scheduler job."""


@dataclass(frozen=True)
class CancellationResult:
    """Outcome of a scheduler cancellation request.

    Args:
        job_id: Job identifier requested for cancellation.
        accepted: Whether the scheduler accepted the cancellation request.
        status: Resulting cancellation state.
        reason: Human-readable cancellation reason or rejection detail.
    """

    job_id: str
    accepted: bool
    status: str
    reason: str

    def __post_init__(self) -> None:
        if not self.job_id:
            raise ValueError("CancellationResult.job_id must be non-empty")
        if self.status not in {"cancelled", "not_found", "unsupported"}:
            raise ValueError("CancellationResult.status is not supported")
        if not self.reason:
            raise ValueError("CancellationResult.reason must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible cancellation mapping."""

        return {
            "job_id": self.job_id,
            "accepted": self.accepted,
            "status": self.status,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class BatchRun:
    """Result from a deterministic local batch run."""

    scheduler: str
    max_workers: int
    results: tuple[JobResult, ...]

    def __post_init__(self) -> None:
        if not self.scheduler:
            raise ValueError("BatchRun.scheduler must be non-empty")
        if self.max_workers < 1:
            raise ValueError("BatchRun.max_workers must be positive")

    @property
    def succeeded(self) -> bool:
        """Whether every job completed successfully."""

        return all(result.status == "ok" for result in self.results)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible batch result mapping."""

        return {
            "scheduler": self.scheduler,
            "max_workers": self.max_workers,
            "results": [result.to_dict() for result in self.results],
            "summary": dict(summarize_results(self.results)),
        }


class LocalScheduler:
    """Deterministic in-process scheduler for tests and local batch runs."""

    def __init__(self, handlers: Mapping[str, JobHandler]) -> None:
        if not isinstance(handlers, Mapping):
            raise TypeError("handlers must be a mapping")
        self._handlers = dict(handlers)
        self._cancelled_job_ids: dict[str, str] = {}

    def submit_many(self, jobs: Sequence[JobSpec]) -> tuple[JobResult, ...]:
        """Execute jobs in order with registered local handlers."""

        _validate_unique_job_ids(jobs)
        results: list[JobResult] = []
        for job in jobs:
            results.append(_execute_local_job(job, self._handlers, self._cancelled_job_ids))
        return tuple(results)

    def cancel_job(self, job_id: str, *, reason: str = "cancelled by user") -> CancellationResult:
        """Mark a local job as cancelled before its next execution."""

        if not job_id:
            raise ValueError("job_id must be non-empty")
        if not reason:
            raise ValueError("reason must be non-empty")
        self._cancelled_job_ids[job_id] = reason
        return CancellationResult(job_id=job_id, accepted=True, status="cancelled", reason=reason)


class LocalParallelBatchRunner:
    """Execute a local batch with standard-library worker threads.

    Results are returned in input order even when handlers complete out of
    order. Handlers receive the immutable job payload and must return a mapping.
    """

    def __init__(self, handlers: Mapping[str, JobHandler], *, max_workers: int = 1) -> None:
        if not isinstance(handlers, Mapping):
            raise TypeError("handlers must be a mapping")
        if isinstance(max_workers, bool) or not isinstance(max_workers, int) or max_workers < 1:
            raise ValueError("max_workers must be a positive integer")
        self._handlers = dict(handlers)
        self._max_workers = max_workers
        self._cancelled_job_ids: dict[str, str] = {}

    def run(self, jobs: Sequence[JobSpec]) -> BatchRun:
        """Run jobs locally and return deterministic batch results."""

        _validate_unique_job_ids(jobs)
        if not jobs:
            return BatchRun(scheduler="local-parallel", max_workers=self._max_workers, results=())

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = [
                executor.submit(_execute_local_job, job, self._handlers, dict(self._cancelled_job_ids))
                for job in jobs
            ]
            results = tuple(future.result() for future in futures)
        return BatchRun(scheduler="local-parallel", max_workers=self._max_workers, results=results)

    def submit_many(self, jobs: Sequence[JobSpec]) -> tuple[JobResult, ...]:
        """Run jobs locally and return one result per input job."""

        return self.run(jobs).results

    def cancel_job(self, job_id: str, *, reason: str = "cancelled by user") -> CancellationResult:
        """Mark a local-parallel job as cancelled before its next execution."""

        if not job_id:
            raise ValueError("job_id must be non-empty")
        if not reason:
            raise ValueError("reason must be non-empty")
        self._cancelled_job_ids[job_id] = reason
        return CancellationResult(job_id=job_id, accepted=True, status="cancelled", reason=reason)


def summarize_results(results: Sequence[JobResult]) -> Mapping[str, int]:
    """Count scheduler results by status."""

    summary: dict[str, int] = {}
    for result in results:
        summary[result.status] = summary.get(result.status, 0) + 1
    return MappingProxyType(summary)


def _execute_local_job(
    job: JobSpec,
    handlers: Mapping[str, JobHandler],
    cancelled_job_ids: Mapping[str, str],
) -> JobResult:
    if job.job_id in cancelled_job_ids:
        return JobResult(
            job_id=job.job_id,
            command=job.command,
            status="cancelled",
            error=cancelled_job_ids[job.job_id],
            provenance={"scheduler": "local", "cancelled": True},
        )

    handler = handlers.get(job.command)
    if handler is None:
        return JobResult(
            job_id=job.job_id,
            command=job.command,
            status="error",
            error=f"No local scheduler handler registered for command '{job.command}'",
            provenance={"scheduler": "local"},
        )
    try:
        output = handler(job.payload)
    except Exception as exc:  # pragma: no cover - behavior tested via result
        return JobResult(
            job_id=job.job_id,
            command=job.command,
            status="error",
            error=f"{type(exc).__name__}: {exc}",
            provenance={"scheduler": "local"},
        )
    if not isinstance(output, Mapping):
        return JobResult(
            job_id=job.job_id,
            command=job.command,
            status="error",
            error="Job handler output must be a mapping",
            provenance={"scheduler": "local"},
        )
    return JobResult(
        job_id=job.job_id,
        command=job.command,
        status="ok",
        output=output,
        provenance={"scheduler": "local"},
    )


def _validate_unique_job_ids(jobs: Sequence[JobSpec]) -> None:
    seen: set[str] = set()
    for job in jobs:
        if job.job_id in seen:
            raise ValueError(f"Duplicate job_id '{job.job_id}'")
        seen.add(job.job_id)
