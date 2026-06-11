"""Benchmark taxonomy and stable naming helpers.

Benchmark IDs use five slug components:
``workstream.kernel.backend.size.variant``. The convention makes benchmark
outputs comparable across Python, JAX, Rust, and future runners without
depending on a specific execution framework.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


_SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class BenchmarkKind(str, Enum):
    """Benchmark intent categories used for scheduling and reporting."""

    MICRO = "micro"
    INTEGRATION = "integration"
    SCIENTIFIC_VALIDATION = "scientific_validation"
    END_TO_END_WORKFLOW = "end_to_end_workflow"


class BenchmarkWorkstream(str, Enum):
    """Top-level benchmark workstreams covered by the foundation taxonomy."""

    NUMERICAL = "numerical"
    WORKFLOW = "workflow"
    HPC = "hpc"
    AI = "ai"
    UX = "ux"


@dataclass(frozen=True)
class BenchmarkFamily:
    """Documented benchmark family in the Rietveld Next taxonomy.

    Args:
        workstream: Top-level benchmark workstream.
        kind: Benchmark intent category.
        description: Short developer-facing description.
        default_ci: Whether the family is suitable for default CI.

    Example:
        >>> family = benchmark_families()["numerical_micro"]
        >>> family.workstream.value
        'numerical'
    """

    workstream: BenchmarkWorkstream
    kind: BenchmarkKind
    description: str
    default_ci: bool

    def __post_init__(self) -> None:
        """Validate human-facing taxonomy text."""
        if not isinstance(self.description, str) or not self.description:
            raise ValueError("description must be a non-empty string.")


@dataclass(frozen=True)
class BenchmarkIdentity:
    """Stable benchmark identity.

    Args:
        workstream: Benchmark workstream, such as ``"numerical"``.
        kernel: Kernel, workflow, or operation being measured.
        backend: Implementation backend, such as ``"python"``, ``"jax"``, or
            ``"rust"``.
        size: Dataset size preset or explicit size slug.
        variant: Scientific or implementation variant.

    Example:
        >>> identity = BenchmarkIdentity("numerical", "gaussian_profile", "python", "small", "synthetic")
        >>> identity.benchmark_id()
        'numerical.gaussian_profile.python.small.synthetic'
    """

    workstream: str
    kernel: str
    backend: str
    size: str
    variant: str

    def __post_init__(self) -> None:
        """Validate all benchmark identity components as lowercase slugs."""
        for field_name, value in (
            ("workstream", self.workstream),
            ("kernel", self.kernel),
            ("backend", self.backend),
            ("size", self.size),
            ("variant", self.variant),
        ):
            _validate_slug(value, field_name)

    def benchmark_id(self) -> str:
        """Return ``workstream.kernel.backend.size.variant``."""
        return ".".join((self.workstream, self.kernel, self.backend, self.size, self.variant))

    def to_dict(self) -> dict[str, str]:
        """Return a deterministic JSON-compatible identity mapping."""
        return {
            "workstream": self.workstream,
            "kernel": self.kernel,
            "backend": self.backend,
            "size": self.size,
            "variant": self.variant,
            "benchmark_id": self.benchmark_id(),
        }


def build_benchmark_id(*, workstream: str, kernel: str, backend: str, size: str, variant: str) -> str:
    """Build and validate a benchmark ID.

    Args:
        workstream: Top-level benchmark workstream.
        kernel: Kernel, workflow, or operation name.
        backend: Backend implementation slug.
        size: Dataset size preset or explicit size slug.
        variant: Scientific or implementation variant slug.

    Returns:
        Stable benchmark ID.

    Raises:
        ValueError: If any component is not a lowercase slug.

    Example:
        >>> build_benchmark_id(
        ...     workstream="numerical",
        ...     kernel="gaussian_profile",
        ...     backend="rust",
        ...     size="small",
        ...     variant="synthetic",
        ... )
        'numerical.gaussian_profile.rust.small.synthetic'
    """
    return BenchmarkIdentity(workstream, kernel, backend, size, variant).benchmark_id()


def parse_benchmark_id(benchmark_id: str) -> BenchmarkIdentity:
    """Parse a benchmark ID into its typed identity components.

    Args:
        benchmark_id: ID in ``workstream.kernel.backend.size.variant`` form.

    Returns:
        Parsed benchmark identity.

    Raises:
        ValueError: If the ID has the wrong number of components or invalid
            slug text.
    """
    if not isinstance(benchmark_id, str):
        raise ValueError(f"benchmark_id must be a string, got {benchmark_id!r}.")
    parts = benchmark_id.split(".")
    if len(parts) != 5:
        raise ValueError("benchmark_id must have workstream.kernel.backend.size.variant components.")
    return BenchmarkIdentity(
        workstream=parts[0],
        kernel=parts[1],
        backend=parts[2],
        size=parts[3],
        variant=parts[4],
    )


def benchmark_families() -> dict[str, BenchmarkFamily]:
    """Return the foundation benchmark taxonomy.

    Families that are expensive or environment-dependent are marked
    ``default_ci=False`` so normal CI can skip them by policy.

    Returns:
        Mapping from family slug to documented benchmark family.
    """
    return {
        "numerical_micro": BenchmarkFamily(
            workstream=BenchmarkWorkstream.NUMERICAL,
            kind=BenchmarkKind.MICRO,
            description="Small kernel-level timings for profiles, residuals, and derivatives.",
            default_ci=True,
        ),
        "workflow_integration": BenchmarkFamily(
            workstream=BenchmarkWorkstream.WORKFLOW,
            kind=BenchmarkKind.INTEGRATION,
            description="Multi-component workflow timings with deterministic synthetic inputs.",
            default_ci=False,
        ),
        "hpc_integration": BenchmarkFamily(
            workstream=BenchmarkWorkstream.HPC,
            kind=BenchmarkKind.INTEGRATION,
            description="Scheduler, packaging, and dispatch overhead benchmarks.",
            default_ci=False,
        ),
        "ai_end_to_end": BenchmarkFamily(
            workstream=BenchmarkWorkstream.AI,
            kind=BenchmarkKind.END_TO_END_WORKFLOW,
            description="Tool-grounded agent replay and provenance workflow measurements.",
            default_ci=False,
        ),
        "ux_integration": BenchmarkFamily(
            workstream=BenchmarkWorkstream.UX,
            kind=BenchmarkKind.INTEGRATION,
            description="Visualization and interaction data-transform performance checks.",
            default_ci=False,
        ),
        "scientific_validation": BenchmarkFamily(
            workstream=BenchmarkWorkstream.NUMERICAL,
            kind=BenchmarkKind.SCIENTIFIC_VALIDATION,
            description="Reference-data or cross-software numerical validation benchmarks.",
            default_ci=False,
        ),
    }


def _validate_slug(value: str, field_name: str) -> None:
    if not isinstance(value, str) or _SLUG_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase slug using letters, digits, or underscores, got {value!r}.")
