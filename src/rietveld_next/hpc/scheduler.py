"""Scheduler abstraction and deterministic local scheduler."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence


JobHandler = Callable[[Mapping[str, Any]], Mapping[str, Any]]


@dataclass(frozen=True)
class JobSpec:
    """Scheduler-independent job request."""

    job_id: str
    command: str
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.job_id:
            raise ValueError("JobSpec.job_id must be non-empty")
        if not self.command:
            raise ValueError("JobSpec.command must be non-empty")
        if not isinstance(self.payload, Mapping):
            raise TypeError("JobSpec.payload must be a mapping")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))


@dataclass(frozen=True)
class JobResult:
    """Result from a scheduler job."""

    job_id: str
    command: str
    status: str
    output: Mapping[str, Any] | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"queued", "running", "ok", "error", "cancelled"}:
            raise ValueError("JobResult.status is not a supported scheduler status")
        if self.output is not None:
            object.__setattr__(self, "output", MappingProxyType(dict(self.output)))


class LocalScheduler:
    """Deterministic in-process scheduler for tests and local batch runs."""

    def __init__(self, handlers: Mapping[str, JobHandler]) -> None:
        if not isinstance(handlers, Mapping):
            raise TypeError("handlers must be a mapping")
        self._handlers = dict(handlers)

    def submit_many(self, jobs: Sequence[JobSpec]) -> tuple[JobResult, ...]:
        """Execute jobs in order with registered local handlers."""

        _validate_unique_job_ids(jobs)
        results: list[JobResult] = []
        for job in jobs:
            handler = self._handlers.get(job.command)
            if handler is None:
                results.append(
                    JobResult(
                        job_id=job.job_id,
                        command=job.command,
                        status="error",
                        error=f"No local scheduler handler registered for command '{job.command}'",
                    )
                )
                continue
            try:
                output = handler(job.payload)
            except Exception as exc:  # pragma: no cover - behavior tested via result
                results.append(
                    JobResult(
                        job_id=job.job_id,
                        command=job.command,
                        status="error",
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
                continue
            if not isinstance(output, Mapping):
                results.append(
                    JobResult(
                        job_id=job.job_id,
                        command=job.command,
                        status="error",
                        error="Job handler output must be a mapping",
                    )
                )
                continue
            results.append(JobResult(job_id=job.job_id, command=job.command, status="ok", output=output))
        return tuple(results)


def summarize_results(results: Sequence[JobResult]) -> Mapping[str, int]:
    """Count scheduler results by status."""

    summary: dict[str, int] = {}
    for result in results:
        summary[result.status] = summary.get(result.status, 0) + 1
    return MappingProxyType(summary)


def _validate_unique_job_ids(jobs: Sequence[JobSpec]) -> None:
    seen: set[str] = set()
    for job in jobs:
        if job.job_id in seen:
            raise ValueError(f"Duplicate job_id '{job.job_id}'")
        seen.add(job.job_id)
