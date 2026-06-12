"""Lightweight validation baseline utilities for M34.

The helpers in this module are deterministic and dependency-free. They provide
schema-shaped records, smoke checks, and placeholders for external comparison
backends without running expensive scientific validation in normal CI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import importlib
import re
from pathlib import Path
from typing import Any


VALIDATION_SCHEMA_VERSION = "validation-report-v1"
GOLDEN_DATASET_SCHEMA_VERSION = "golden-dataset-v1"


@dataclass(frozen=True)
class TolerancePolicy:
    """Numerical tolerance policy for a validation case.

    Args:
        absolute: Maximum absolute difference.
        relative: Maximum relative difference.
        units: Units for the compared quantity.
        rationale: Why this tolerance is appropriate for the fixture.
    """

    absolute: float
    relative: float
    units: str
    rationale: str

    def __post_init__(self) -> None:
        """Validate finite non-negative tolerances and required metadata."""
        _finite_nonnegative(self.absolute, "absolute")
        _finite_nonnegative(self.relative, "relative")
        if not self.units:
            raise ValueError("units must be non-empty.")
        if not self.rationale:
            raise ValueError("rationale must be non-empty.")

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible tolerance metadata."""
        return {
            "absolute": self.absolute,
            "relative": self.relative,
            "units": self.units,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class GoldenDataset:
    """Small deterministic validation fixture descriptor.

    Args:
        id: Stable fixture ID.
        domain: Scientific domain or package area.
        description: Human-readable fixture purpose.
        axis_units: Units for the x-axis.
        intensity_units: Units for the y-axis.
        x: Axis values.
        y: Signal values.
        provenance: Fixture provenance and generation metadata.
    """

    id: str
    domain: str
    description: str
    axis_units: str
    intensity_units: str
    x: tuple[float, ...]
    y: tuple[float, ...]
    provenance: dict[str, str] = field(default_factory=dict)
    schema_version: str = GOLDEN_DATASET_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate fixture shape, metadata, and finite values."""
        _identifier(self.id, "id")
        for name, value in (
            ("domain", self.domain),
            ("description", self.description),
            ("axis_units", self.axis_units),
            ("intensity_units", self.intensity_units),
        ):
            if not value:
                raise ValueError(f"{name} must be non-empty.")
        if len(self.x) != len(self.y):
            raise ValueError("x and y must have the same length.")
        if not self.x:
            raise ValueError("golden datasets require at least one sample.")
        for index, value in enumerate((*self.x, *self.y)):
            _finite_number(value, f"sample[{index}]")

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible fixture metadata."""
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "domain": self.domain,
            "description": self.description,
            "axis_units": self.axis_units,
            "intensity_units": self.intensity_units,
            "x": list(self.x),
            "y": list(self.y),
            "provenance": dict(sorted(self.provenance.items())),
        }


@dataclass(frozen=True)
class ValidationCase:
    """Single validation case record.

    Args:
        id: Stable case ID.
        dataset_id: Golden dataset ID used by the case.
        expected: Expected scalar summary value.
        observed: Observed scalar summary value.
        tolerance: Numerical tolerance policy.
        expensive: Whether this case is opt-in and excluded from default CI.
        backend: Tool or package that produced the observed value.
    """

    id: str
    dataset_id: str
    expected: float
    observed: float
    tolerance: TolerancePolicy
    expensive: bool = False
    backend: str = "python"

    def __post_init__(self) -> None:
        """Validate case metadata and scalar values."""
        _identifier(self.id, "id")
        _identifier(self.dataset_id, "dataset_id")
        _finite_number(self.expected, "expected")
        _finite_number(self.observed, "observed")
        if not isinstance(self.expensive, bool):
            raise ValueError("expensive must be a boolean.")
        if not self.backend:
            raise ValueError("backend must be non-empty.")

    @property
    def passed(self) -> bool:
        """Return whether observed and expected values satisfy tolerances."""
        difference = abs(self.observed - self.expected)
        scale = max(abs(self.expected), 1.0)
        return difference <= max(self.tolerance.absolute, self.tolerance.relative * scale)

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible case metadata."""
        return {
            "id": self.id,
            "dataset_id": self.dataset_id,
            "backend": self.backend,
            "expected": self.expected,
            "observed": self.observed,
            "passed": self.passed,
            "expensive": self.expensive,
            "tolerance": self.tolerance.to_dict(),
        }


@dataclass(frozen=True)
class ValidationReport:
    """Validation report summary.

    Args:
        cases: Validation cases included in the report.
        known_limitations: Explicit limitations that keep the report honest.
        generated_by: Tool or actor that generated the report.
    """

    cases: tuple[ValidationCase, ...]
    known_limitations: tuple[str, ...] = ()
    generated_by: str = "rietveld-next.validation"
    schema_version: str = VALIDATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate report metadata."""
        if not self.generated_by:
            raise ValueError("generated_by must be non-empty.")
        if len({case.id for case in self.cases}) != len(self.cases):
            raise ValueError("validation case IDs must be unique.")
        for limitation in self.known_limitations:
            if not limitation:
                raise ValueError("known limitations must be non-empty strings.")

    @property
    def passed(self) -> bool:
        """Return whether all included cases passed."""
        return all(case.passed for case in self.cases)

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible report metadata."""
        passed_count = sum(1 for case in self.cases if case.passed)
        return {
            "schema_version": self.schema_version,
            "generated_by": self.generated_by,
            "passed": self.passed,
            "summary": {
                "total": len(self.cases),
                "passed": passed_count,
                "failed": len(self.cases) - passed_count,
                "expensive": sum(1 for case in self.cases if case.expensive),
            },
            "cases": [case.to_dict() for case in sorted(self.cases, key=lambda item: item.id)],
            "known_limitations": list(self.known_limitations),
        }


@dataclass(frozen=True)
class ComparisonResult:
    """External comparison backend result.

    Args:
        backend: External backend name, such as ``GSAS-II``.
        status: ``passed``, ``failed``, or ``placeholder``.
        message: Human-readable result or limitation.
    """

    backend: str
    status: str
    message: str

    def __post_init__(self) -> None:
        """Validate comparison result metadata."""
        if not self.backend:
            raise ValueError("backend must be non-empty.")
        if self.status not in {"passed", "failed", "placeholder"}:
            raise ValueError("status must be passed, failed, or placeholder.")
        if not self.message:
            raise ValueError("message must be non-empty.")

    def to_dict(self) -> dict[str, str]:
        """Return deterministic JSON-compatible comparison metadata."""
        return {"backend": self.backend, "status": self.status, "message": self.message}


@dataclass(frozen=True)
class ComparisonHarness:
    """External comparison harness metadata.

    Args:
        backend: External backend name.
        command: Optional command used for available backends.
        placeholder_reason: Required reason for unavailable backends.
    """

    backend: str
    command: tuple[str, ...] = ()
    placeholder_reason: str | None = None

    def __post_init__(self) -> None:
        """Validate harness metadata."""
        if not self.backend:
            raise ValueError("backend must be non-empty.")
        if self.command and self.placeholder_reason:
            raise ValueError("command and placeholder_reason are mutually exclusive.")
        if not self.command and not self.placeholder_reason:
            raise ValueError("placeholder_reason is required when no command is configured.")

    def dry_run(self) -> ComparisonResult:
        """Return a deterministic non-executing comparison result."""
        if self.placeholder_reason:
            return ComparisonResult(self.backend, "placeholder", self.placeholder_reason)
        return ComparisonResult(self.backend, "passed", f"Dry-run command configured: {' '.join(self.command)}")


@dataclass(frozen=True)
class DocumentationIssue:
    """Single documentation link issue."""

    path: str
    target: str
    message: str


@dataclass(frozen=True)
class ReleaseChecklist:
    """Release validation checklist outcome."""

    required_checks: tuple[str, ...]
    completed_checks: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate checklist labels."""
        for check in (*self.required_checks, *self.completed_checks):
            if not check:
                raise ValueError("check names must be non-empty.")

    @property
    def missing_checks(self) -> tuple[str, ...]:
        """Return required checks that have not been completed."""
        completed = set(self.completed_checks)
        return tuple(check for check in self.required_checks if check not in completed)

    @property
    def ready(self) -> bool:
        """Return whether all required checks are complete."""
        return not self.missing_checks


def create_synthetic_profile_dataset(sample_count: int = 5) -> GoldenDataset:
    """Create a deterministic tiny synthetic profile fixture.

    Args:
        sample_count: Number of samples to generate.

    Returns:
        Golden dataset with a simple triangular profile.

    Raises:
        ValueError: If ``sample_count`` is less than three.
    """
    if isinstance(sample_count, bool) or not isinstance(sample_count, int) or sample_count < 3:
        raise ValueError("sample_count must be an integer greater than or equal to 3.")
    center = (sample_count - 1) / 2.0
    x = tuple(float(index) for index in range(sample_count))
    y = tuple(max(0.0, 1.0 - abs(index - center) / max(center, 1.0)) for index in range(sample_count))
    return GoldenDataset(
        id=f"synthetic_profile_{sample_count}",
        domain="synthetic_profile",
        description="Deterministic triangular profile for validation smoke tests.",
        axis_units="index",
        intensity_units="relative_intensity",
        x=x,
        y=y,
        provenance={"generator": "create_synthetic_profile_dataset", "seed": "deterministic"},
    )


def package_import_smoke_test(packages: tuple[str, ...]) -> tuple[str, ...]:
    """Import packages and return their names in deterministic order.

    Args:
        packages: Fully qualified package names to import.

    Returns:
        Sorted imported package names.

    Raises:
        ImportError: If any package cannot be imported.
        ValueError: If a package name is empty.
    """
    imported: list[str] = []
    for name in packages:
        if not name:
            raise ValueError("package names must be non-empty.")
        importlib.import_module(name)
        imported.append(name)
    return tuple(sorted(imported))


def validation_ci_matrix() -> tuple[dict[str, str], ...]:
    """Return the documented lightweight CI matrix.

    Returns:
        OS/Python combinations intended for normal validation gates.
    """
    return (
        {"os": "ubuntu-latest", "python": "3.11"},
        {"os": "ubuntu-latest", "python": "3.12"},
        {"os": "macos-latest", "python": "3.12"},
        {"os": "windows-latest", "python": "3.12"},
    )


def check_markdown_links(root: Path, markdown_paths: tuple[Path, ...]) -> tuple[DocumentationIssue, ...]:
    """Check local Markdown links without network access.

    Args:
        root: Repository root.
        markdown_paths: Markdown files to inspect.

    Returns:
        Deterministic tuple of missing local link issues.
    """
    repository_root = root.resolve()
    issues: list[DocumentationIssue] = []
    pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in sorted(markdown_paths):
        text = path.read_text(encoding="utf-8")
        for target in pattern.findall(text):
            if _is_external_or_anchor(target):
                continue
            target_path = (path.parent / target.split("#", 1)[0]).resolve()
            try:
                target_path.relative_to(repository_root)
            except ValueError:
                issues.append(DocumentationIssue(str(path.relative_to(repository_root)), target, "Link escapes repository."))
                continue
            if not target_path.exists():
                issues.append(
                    DocumentationIssue(str(path.resolve().relative_to(repository_root)), target, "Local link target is missing.")
                )
    return tuple(sorted(issues, key=lambda issue: (issue.path, issue.target, issue.message)))


def _is_external_or_anchor(target: str) -> bool:
    return (
        target.startswith("#")
        or "://" in target
        or target.startswith("mailto:")
        or target.startswith("tel:")
    )


def _identifier(value: str, path: str) -> None:
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.:-]*", value):
        raise ValueError(f"{path} must be a stable identifier.")


def _finite_nonnegative(value: float, path: str) -> None:
    _finite_number(value, path)
    if value < 0:
        raise ValueError(f"{path} must be non-negative.")


def _finite_number(value: float, path: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float) or value != value or value in {float("inf"), float("-inf")}:
        raise ValueError(f"{path} must be a finite number.")
