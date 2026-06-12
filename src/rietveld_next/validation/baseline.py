"""Lightweight validation baseline utilities for M34.

The helpers in this module are deterministic and dependency-free. They provide
schema-shaped records, smoke checks, and placeholders for external comparison
backends without running expensive scientific validation in normal CI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import importlib
import os
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
        return ComparisonResult(self.backend, "placeholder", f"Dry-run command configured but not executed: {' '.join(self.command)}")


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


@dataclass(frozen=True)
class PerformanceRegressionThreshold:
    """Performance regression threshold for opt-in benchmark checks."""

    max_relative_slowdown: float
    max_absolute_seconds: float

    def __post_init__(self) -> None:
        """Validate finite non-negative threshold values."""
        _finite_nonnegative(self.max_relative_slowdown, "max_relative_slowdown")
        _finite_nonnegative(self.max_absolute_seconds, "max_absolute_seconds")


@dataclass(frozen=True)
class PerformanceRegressionResult:
    """Performance regression comparison outcome."""

    name: str
    baseline_seconds: float
    current_seconds: float
    threshold: PerformanceRegressionThreshold

    def __post_init__(self) -> None:
        """Validate comparison metadata."""
        _identifier(self.name, "name")
        _finite_nonnegative(self.baseline_seconds, "baseline_seconds")
        _finite_nonnegative(self.current_seconds, "current_seconds")

    @property
    def delta_seconds(self) -> float:
        """Return current minus baseline runtime."""
        return self.current_seconds - self.baseline_seconds

    @property
    def relative_slowdown(self) -> float:
        """Return relative slowdown, using 1.0 second as zero-baseline scale."""
        return self.delta_seconds / max(self.baseline_seconds, 1.0)

    @property
    def passed(self) -> bool:
        """Return whether the current timing is within threshold."""
        return (
            self.delta_seconds <= self.threshold.max_absolute_seconds
            and self.relative_slowdown <= self.threshold.max_relative_slowdown
        )

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible performance metadata."""
        return {
            "name": self.name,
            "baseline_seconds": self.baseline_seconds,
            "current_seconds": self.current_seconds,
            "delta_seconds": self.delta_seconds,
            "relative_slowdown": self.relative_slowdown,
            "passed": self.passed,
            "threshold": {
                "max_relative_slowdown": self.threshold.max_relative_slowdown,
                "max_absolute_seconds": self.threshold.max_absolute_seconds,
            },
        }


@dataclass(frozen=True)
class VisualRegressionSnapshot:
    """Framework-neutral visual regression snapshot metadata."""

    view_id: str
    width_px: int
    height_px: int
    checksum: str

    def __post_init__(self) -> None:
        """Validate visual snapshot metadata without reading image files."""
        _identifier(self.view_id, "view_id")
        for name, value in (("width_px", self.width_px), ("height_px", self.height_px)):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer.")
        if not re.fullmatch(r"[0-9a-f]{16,64}", self.checksum):
            raise ValueError("checksum must be lowercase hexadecimal with 16 to 64 characters.")

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible visual snapshot metadata."""
        return {
            "view_id": self.view_id,
            "width_px": self.width_px,
            "height_px": self.height_px,
            "checksum": self.checksum,
        }


@dataclass(frozen=True)
class SecurityScanPolicy:
    """Simple local security scan policy for committed text files."""

    forbidden_patterns: tuple[str, ...] = (
        r"BEGIN PRIVATE KEY",
        r"aws_secret_access_key\s*=",
        r"ghp_[A-Za-z0-9_]{20,}",
    )

    def scan_text(self, text: str) -> tuple[str, ...]:
        """Return forbidden pattern labels found in text."""
        findings: list[str] = []
        for pattern in self.forbidden_patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                findings.append(pattern)
        return tuple(findings)


def validate_golden_dataset_dict(data: dict[str, Any]) -> None:
    """Validate a golden dataset mapping against the M34 fixture contract."""
    _require_mapping(data, "golden_dataset")
    _require_keys(data, ("schema_version", "id", "domain", "description", "axis_units", "intensity_units", "x", "y", "provenance"), "golden_dataset")
    if data["schema_version"] != GOLDEN_DATASET_SCHEMA_VERSION:
        raise ValueError("golden_dataset.schema_version is unsupported.")
    GoldenDataset(
        id=data["id"],
        domain=data["domain"],
        description=data["description"],
        axis_units=data["axis_units"],
        intensity_units=data["intensity_units"],
        x=tuple(data["x"]),
        y=tuple(data["y"]),
        provenance=dict(data["provenance"]),
    )


def validate_validation_report_dict(data: dict[str, Any]) -> None:
    """Validate a validation report mapping against the M34 report contract."""
    _require_mapping(data, "validation_report")
    _require_keys(data, ("schema_version", "generated_by", "passed", "summary", "cases", "known_limitations"), "validation_report")
    if data["schema_version"] != VALIDATION_SCHEMA_VERSION:
        raise ValueError("validation_report.schema_version is unsupported.")
    if not isinstance(data["passed"], bool):
        raise ValueError("validation_report.passed must be a boolean.")
    if not isinstance(data["cases"], list):
        raise ValueError("validation_report.cases must be a list.")
    for index, case in enumerate(data["cases"]):
        _validate_case_dict(case, f"validation_report.cases[{index}]")
    if not isinstance(data["known_limitations"], list) or any(not isinstance(item, str) or not item for item in data["known_limitations"]):
        raise ValueError("validation_report.known_limitations must contain non-empty strings.")
    summary = data["summary"]
    _require_mapping(summary, "validation_report.summary")
    _require_keys(summary, ("total", "passed", "failed", "expensive"), "validation_report.summary")
    expected_total = len(data["cases"])
    passed_count = sum(1 for case in data["cases"] if bool(case["passed"]))
    if summary["total"] != expected_total or summary["passed"] != passed_count or summary["failed"] != expected_total - passed_count:
        raise ValueError("validation_report.summary counts do not match cases.")


def gsasii_comparison_harness(command: tuple[str, ...] | None = None) -> ComparisonHarness:
    """Return the standard GSAS-II comparison harness metadata."""
    if command is None:
        return ComparisonHarness(
            "GSAS-II",
            placeholder_reason="GSAS-II comparison is offline until redistributable fixtures are approved.",
        )
    return ComparisonHarness("GSAS-II", command=command)


def fullprof_comparison_placeholder() -> ComparisonHarness:
    """Return the standard FullProf placeholder harness."""
    return ComparisonHarness("FullProf", placeholder_reason="FullProf fixtures are not bundled because redistribution terms are unresolved.")


def topas_comparison_placeholder() -> ComparisonHarness:
    """Return the standard TOPAS placeholder harness."""
    return ComparisonHarness("TOPAS", placeholder_reason="TOPAS fixtures are not bundled because redistribution terms are unresolved.")


def compare_performance_regression(
    *,
    name: str,
    baseline_seconds: float,
    current_seconds: float,
    threshold: PerformanceRegressionThreshold,
) -> PerformanceRegressionResult:
    """Compare current benchmark timing against an opt-in baseline."""
    return PerformanceRegressionResult(name, baseline_seconds, current_seconds, threshold)


def standard_release_checklist(completed_checks: tuple[str, ...] = ()) -> ReleaseChecklist:
    """Return the standard M34 release validation checklist."""
    return ReleaseChecklist(
        required_checks=(
            "source-layout",
            "package-imports",
            "unit-tests",
            "schema-parse",
            "docs-links",
            "validation-limitations",
            "release-manifest",
        ),
        completed_checks=completed_checks,
    )


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
    repository_root = _canonical_path(root)
    issues: list[DocumentationIssue] = []
    pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in sorted(markdown_paths):
        text = path.read_text(encoding="utf-8")
        resolved_path = _canonical_path(path)
        for target in pattern.findall(text):
            if _is_external_or_anchor(target):
                continue
            target_path = _canonical_path(path.parent / target.split("#", 1)[0])
            try:
                target_path.relative_to(repository_root)
            except ValueError:
                issues.append(
                    DocumentationIssue(
                        _relative_path_text(resolved_path, repository_root),
                        target,
                        "Link escapes repository.",
                    )
                )
                continue
            if not target_path.exists():
                issues.append(
                    DocumentationIssue(
                        _relative_path_text(resolved_path, repository_root),
                        target,
                        "Local link target is missing.",
                    )
                )
    return tuple(sorted(issues, key=lambda issue: (issue.path, issue.target, issue.message)))


def _canonical_path(path: Path) -> Path:
    return Path(os.path.realpath(path))


def _relative_path_text(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


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


def _require_mapping(data: Any, path: str) -> None:
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be an object.")


def _require_keys(data: dict[str, Any], keys: tuple[str, ...], path: str) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise ValueError(f"{path} is missing required keys: {', '.join(missing)}.")


def _validate_case_dict(data: Any, path: str) -> None:
    _require_mapping(data, path)
    _require_keys(
        data,
        ("id", "dataset_id", "backend", "expected", "observed", "passed", "expensive", "tolerance"),
        path,
    )
    if not isinstance(data["passed"], bool) or not isinstance(data["expensive"], bool):
        raise ValueError(f"{path}.passed and {path}.expensive must be booleans.")
    _require_mapping(data["tolerance"], f"{path}.tolerance")
    _require_keys(data["tolerance"], ("absolute", "relative", "units", "rationale"), f"{path}.tolerance")
    tolerance = TolerancePolicy(
        absolute=data["tolerance"]["absolute"],
        relative=data["tolerance"]["relative"],
        units=data["tolerance"]["units"],
        rationale=data["tolerance"]["rationale"],
    )
    ValidationCase(
        id=data["id"],
        dataset_id=data["dataset_id"],
        expected=data["expected"],
        observed=data["observed"],
        tolerance=tolerance,
        expensive=data["expensive"],
        backend=data["backend"],
    )


def _finite_nonnegative(value: float, path: str) -> None:
    _finite_number(value, path)
    if value < 0:
        raise ValueError(f"{path} must be non-negative.")


def _finite_number(value: float, path: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float) or value != value or value in {float("inf"), float("-inf")}:
        raise ValueError(f"{path} must be a finite number.")
