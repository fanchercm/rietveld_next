"""Optional Dask and Ray scheduler adapter skeletons."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from typing import Any, Sequence

from rietveld_next.hpc.scheduler import CancellationResult, JobResult, JobSpec


@dataclass(frozen=True)
class AdapterAvailability:
    """Availability report for an optional scheduler backend."""

    backend: str
    available: bool
    reason: str

    def __post_init__(self) -> None:
        if not self.backend:
            raise ValueError("AdapterAvailability.backend must be non-empty")
        if not self.reason:
            raise ValueError("AdapterAvailability.reason must be non-empty")

    @property
    def status(self) -> str:
        """Return ``"available"`` or ``"unavailable"``."""

        return "available" if self.available else "unavailable"

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible availability mapping."""

        return {"backend": self.backend, "status": self.status, "available": self.available, "reason": self.reason}


class OptionalSchedulerAdapter:
    """Skeleton adapter for optional distributed schedulers.

    The skeleton never starts a client or connects to a cluster. It reports
    dependency availability and returns skipped job results until a concrete
    adapter is implemented.
    """

    def __init__(self, backend: str, module_name: str, *, dependency_available: bool | None = None) -> None:
        if not backend:
            raise ValueError("backend must be non-empty")
        if not module_name:
            raise ValueError("module_name must be non-empty")
        self._backend = backend
        self._module_name = module_name
        self._dependency_available = dependency_available

    def availability(self) -> AdapterAvailability:
        """Return optional dependency availability without importing it."""

        available = find_spec(self._module_name) is not None if self._dependency_available is None else self._dependency_available
        if available:
            reason = f"{self._backend} dependency is importable; execution adapter is a skeleton."
        else:
            reason = f"{self._backend} dependency is not installed."
        return AdapterAvailability(backend=self._backend, available=available, reason=reason)

    def submit_many(self, jobs: Sequence[JobSpec]) -> tuple[JobResult, ...]:
        """Return skipped results for every job."""

        availability = self.availability()
        reason = (
            availability.reason
            if not availability.available
            else f"{self._backend} execution is not implemented in the framework-free foundation."
        )
        return tuple(
            JobResult(
                job_id=job.job_id,
                command=job.command,
                status="skipped",
                error=reason,
                provenance={"scheduler": self._backend, "availability": availability.status},
            )
            for job in jobs
        )

    def cancel_job(self, job_id: str, *, reason: str = "cancelled by user") -> CancellationResult:
        """Report cancellation as unsupported for skeleton adapters."""

        if not job_id:
            raise ValueError("job_id must be non-empty")
        if not reason:
            raise ValueError("reason must be non-empty")
        return CancellationResult(
            job_id=job_id,
            accepted=False,
            status="unsupported",
            reason=f"{self._backend} skeleton adapter does not manage live jobs.",
        )


class DaskAdapter(OptionalSchedulerAdapter):
    """Dask adapter skeleton with deterministic skip behavior."""

    def __init__(self, *, dependency_available: bool | None = None) -> None:
        super().__init__("dask", "dask", dependency_available=dependency_available)


class RayAdapter(OptionalSchedulerAdapter):
    """Ray adapter skeleton with deterministic skip behavior."""

    def __init__(self, *, dependency_available: bool | None = None) -> None:
        super().__init__("ray", "ray", dependency_available=dependency_available)
