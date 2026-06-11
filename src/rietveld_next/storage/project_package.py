"""Read-only Rietveld project package loader."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from rietveld_next.core.model import Project
from rietveld_next.core.schema import project_from_json, project_to_json


class ProjectPackageError(ValueError):
    """Raised when a project package cannot be read or validated."""


@dataclass(frozen=True)
class ProjectPackage:
    """Validated project package loaded from disk.

    Args:
        root: Package directory.
        project: Validated project metadata.
        manifest: Optional package manifest mapping.
    """

    root: Path
    project: Project
    manifest: dict[str, Any]

    @property
    def project_json_path(self) -> Path:
        """Return the canonical project metadata path."""

        return self.root / "project.json"


@dataclass(frozen=True)
class ProjectPackageIntegrityIssue:
    """Single project package integrity finding.

    Args:
        code: Stable issue code for tests and callers.
        path: Package-relative path where the issue was found.
        message: Human-readable explanation.
    """

    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ProjectPackageIntegrityReport:
    """Integrity report for a directory-backed project package."""

    issues: tuple[ProjectPackageIntegrityIssue, ...]

    @property
    def ok(self) -> bool:
        """Return whether the package has no integrity issues."""

        return not self.issues

    def require_ok(self) -> None:
        """Raise ``ProjectPackageError`` when integrity issues are present.

        Raises:
            ProjectPackageError: If at least one integrity issue was collected.
        """

        if self.issues:
            first = self.issues[0]
            raise ProjectPackageError(f"{first.code} at {first.path}: {first.message}")


def read_project_package(package_root: Path) -> ProjectPackage:
    """Read and validate a directory-backed Rietveld project package.

    The foundation package layout requires ``project.json`` at the package
    root and treats ``manifest.json`` as optional metadata. This reader is
    intentionally read-only and never creates, overwrites, or repairs files.

    Args:
        package_root: Directory containing package metadata.

    Returns:
        Loaded project package.

    Raises:
        ProjectPackageError: If required files are missing, corrupt, or not
            schema-valid.
    """

    root = Path(package_root)
    if not root.exists():
        raise ProjectPackageError(f"Project package does not exist: {root}")
    if not root.is_dir():
        raise ProjectPackageError(f"Project package root must be a directory: {root}")

    project_path = root / "project.json"
    if not project_path.is_file():
        raise ProjectPackageError(f"Project package is missing required metadata file: {project_path}")

    try:
        project_payload = project_path.read_text(encoding="utf-8")
        project = project_from_json(project_payload)
    except Exception as exc:
        raise ProjectPackageError(f"Failed to read valid project metadata from {project_path}: {exc}") from exc

    manifest_path = root / "manifest.json"
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        if not manifest_path.is_file():
            raise ProjectPackageError(f"Package manifest path is not a file: {manifest_path}")
        try:
            decoded = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ProjectPackageError(f"Package manifest is not valid JSON: {manifest_path}: {exc.msg}") from exc
        if not isinstance(decoded, dict):
            raise ProjectPackageError(f"Package manifest must be a JSON object: {manifest_path}")
        manifest = decoded

    return ProjectPackage(root=root, project=project, manifest=manifest)


def write_project_package(
    package_root: Path,
    project: Project,
    *,
    manifest: dict[str, Any] | None = None,
    overwrite: bool = False,
) -> ProjectPackage:
    """Write a directory-backed Rietveld project package.

    The writer creates ``project.json`` and, when supplied, ``manifest.json``.
    It refuses to overwrite existing files unless ``overwrite=True`` is passed.
    Project JSON is schema-validated before any package files are written.

    Args:
        package_root: Package directory to create or update.
        project: Project metadata model to serialize.
        manifest: Optional JSON-object package manifest.
        overwrite: Whether existing package files may be replaced.

    Returns:
        The package read back through :func:`read_project_package`.

    Raises:
        ProjectPackageError: If the target is unsafe to write, manifest data is
            invalid, or written metadata fails validation.
    """

    root = Path(package_root)
    if root.exists() and not root.is_dir():
        raise ProjectPackageError(f"Project package root must be a directory: {root}")
    if manifest is not None and not isinstance(manifest, dict):
        raise ProjectPackageError("Package manifest must be a JSON object when supplied.")

    project_payload = project_to_json(project)
    root.mkdir(parents=True, exist_ok=True)

    project_path = root / "project.json"
    manifest_path = root / "manifest.json"
    _ensure_can_write(project_path, overwrite)
    if manifest is not None:
        _ensure_can_write(manifest_path, overwrite)

    project_path.write_text(project_payload + "\n", encoding="utf-8")
    if manifest is not None:
        manifest_payload = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
        manifest_path.write_text(manifest_payload + "\n", encoding="utf-8")

    return read_project_package(root)


def check_project_package_integrity(package_root: Path) -> ProjectPackageIntegrityReport:
    """Validate the foundation project package layout without mutating files.

    Args:
        package_root: Package directory to inspect.

    Returns:
        Deterministic integrity report.
    """

    root = Path(package_root)
    issues: list[ProjectPackageIntegrityIssue] = []
    if not root.exists():
        return ProjectPackageIntegrityReport(
            (ProjectPackageIntegrityIssue("missing_package_root", ".", f"Package root does not exist: {root}"),)
        )
    if not root.is_dir():
        return ProjectPackageIntegrityReport(
            (ProjectPackageIntegrityIssue("invalid_package_root", ".", "Package root must be a directory."),)
        )

    project_path = root / "project.json"
    if not project_path.is_file():
        issues.append(
            ProjectPackageIntegrityIssue(
                "missing_project_metadata",
                "project.json",
                "Required project metadata file is missing.",
            )
        )
    else:
        try:
            project_from_json(project_path.read_text(encoding="utf-8"))
        except Exception as exc:
            issues.append(
                ProjectPackageIntegrityIssue(
                    "invalid_project_metadata",
                    "project.json",
                    f"Project metadata is not valid: {exc}",
                )
            )

    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        if not manifest_path.is_file():
            issues.append(
                ProjectPackageIntegrityIssue(
                    "invalid_manifest_path",
                    "manifest.json",
                    "Package manifest path is not a file.",
                )
            )
        else:
            try:
                decoded = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                issues.append(
                    ProjectPackageIntegrityIssue(
                        "invalid_manifest_json",
                        "manifest.json",
                        f"Package manifest is not valid JSON: {exc.msg}.",
                    )
                )
            else:
                if not isinstance(decoded, dict):
                    issues.append(
                        ProjectPackageIntegrityIssue(
                            "invalid_manifest",
                            "manifest.json",
                            "Package manifest must be a JSON object.",
                        )
                    )

    return ProjectPackageIntegrityReport(tuple(sorted(issues, key=lambda issue: (issue.path, issue.code))))


def _ensure_can_write(path: Path, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise ProjectPackageError(f"Refusing to overwrite existing package file without overwrite=True: {path}")
