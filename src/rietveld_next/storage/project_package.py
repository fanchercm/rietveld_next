"""Read-only Rietveld project package loader."""

from __future__ import annotations

from dataclasses import dataclass, field
import gzip
import json
from pathlib import Path
from typing import Any, Literal, Mapping

from rietveld_next.core.model import Project
from rietveld_next.core.schema import project_from_json, project_to_json


ProjectPackageCompression = Literal["none", "gzip"]
_PROJECT_JSON = "project.json"
_PROJECT_JSON_GZIP = "project.json.gz"
_IMPORT_WARNING_REPORT_VERSION = "1.0.0"


class ProjectPackageError(ValueError):
    """Raised when a project package cannot be read or validated."""


@dataclass(frozen=True)
class ProjectImportWarning:
    """Non-blocking warning emitted while importing a project package.

    Args:
        code: Stable warning code for tests and callers.
        path: Package-relative path associated with the warning.
        message: Human-readable warning text.
        severity: Warning severity. Only ``"warning"`` is currently supported.
    """

    code: str
    path: str
    message: str
    severity: Literal["warning"] = "warning"

    def __post_init__(self) -> None:
        """Validate the warning record fields."""

        for name, value in (("code", self.code), ("path", self.path), ("message", self.message)):
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} must be a non-empty string.")
        if self.severity != "warning":
            raise ValueError(f"severity must be 'warning', got {self.severity!r}.")

    def to_dict(self) -> dict[str, str]:
        """Return the deterministic JSON-compatible warning mapping."""

        return {
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "severity": self.severity,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ProjectImportWarning:
        """Build a warning from a JSON-compatible mapping.

        Args:
            payload: Decoded warning mapping.

        Returns:
            Validated import warning.

        Raises:
            ValueError: If the payload is missing required fields.
        """

        if not isinstance(payload, Mapping):
            raise ValueError("import warning payload must be a JSON object.")
        try:
            return cls(
                code=payload["code"],
                path=payload["path"],
                message=payload["message"],
                severity=payload.get("severity", "warning"),
            )
        except KeyError as exc:
            raise ValueError(f"import warning payload is missing {exc.args[0]}.") from exc


@dataclass(frozen=True)
class ProjectImportWarningReport:
    """Deterministic report for non-blocking project import warnings.

    Args:
        warnings: Warning records in deterministic order.
        format_version: Report format version.
    """

    warnings: tuple[ProjectImportWarning, ...]
    format_version: str = _IMPORT_WARNING_REPORT_VERSION

    def __post_init__(self) -> None:
        """Validate and normalize the report contents."""

        if self.format_version != _IMPORT_WARNING_REPORT_VERSION:
            raise ValueError(
                f"format_version must be {_IMPORT_WARNING_REPORT_VERSION!r}, got {self.format_version!r}."
            )
        object.__setattr__(self, "warnings", tuple(self.warnings))
        for warning in self.warnings:
            if not isinstance(warning, ProjectImportWarning):
                raise ValueError("warnings must contain ProjectImportWarning records.")

    @property
    def ok(self) -> bool:
        """Return whether the import completed without warnings."""

        return not self.warnings

    def to_dict(self) -> dict[str, object]:
        """Return the deterministic JSON-compatible report mapping."""

        return {
            "format_version": self.format_version,
            "warnings": [warning.to_dict() for warning in self.warnings],
        }

    def to_json(self) -> str:
        """Return deterministic compact JSON for the warning report."""

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ProjectImportWarningReport:
        """Build a warning report from a JSON-compatible mapping.

        Args:
            payload: Decoded warning report mapping.

        Returns:
            Validated import warning report.

        Raises:
            ValueError: If the payload is malformed.
        """

        if not isinstance(payload, Mapping):
            raise ValueError("import warning report must be a JSON object.")
        raw_warnings = payload.get("warnings")
        if not isinstance(raw_warnings, list):
            raise ValueError("import warning report warnings must be a JSON array.")
        return cls(
            warnings=tuple(ProjectImportWarning.from_dict(item) for item in raw_warnings),
            format_version=payload.get("format_version", ""),
        )

    @classmethod
    def from_json(cls, payload: str) -> ProjectImportWarningReport:
        """Build a warning report from JSON text.

        Args:
            payload: JSON-encoded warning report.

        Returns:
            Validated import warning report.

        Raises:
            ValueError: If the JSON is malformed or not report-shaped.
        """

        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"import warning report is not valid JSON: {exc.msg}.") from exc
        return cls.from_dict(decoded)


@dataclass(frozen=True)
class ProjectPackage:
    """Validated project package loaded from disk.

    Args:
        root: Package directory.
        project: Validated project metadata.
        manifest: Optional package manifest mapping.
        compression: Compression used for project metadata.
        import_warnings: Non-blocking import warning report.
    """

    root: Path
    project: Project
    manifest: dict[str, Any]
    compression: ProjectPackageCompression = "none"
    import_warnings: ProjectImportWarningReport = field(
        default_factory=lambda: ProjectImportWarningReport(())
    )

    @property
    def project_json_path(self) -> Path:
        """Return the canonical project metadata path."""

        return self.root / (_PROJECT_JSON_GZIP if self.compression == "gzip" else _PROJECT_JSON)


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

    The foundation package layout requires ``project.json`` or
    ``project.json.gz`` at the package root and treats ``manifest.json`` as
    optional metadata. This reader is intentionally read-only and never creates,
    overwrites, or repairs files.

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

    project_path, compression = _select_project_metadata_path(root)
    warnings: list[ProjectImportWarning] = []

    try:
        project_payload = _read_project_payload(project_path, compression)
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
    else:
        warnings.append(
            ProjectImportWarning(
                code="missing_manifest",
                path="manifest.json",
                message="Optional package manifest is missing; import continues without package metadata.",
            )
        )

    return ProjectPackage(
        root=root,
        project=project,
        manifest=manifest,
        compression=compression,
        import_warnings=ProjectImportWarningReport(tuple(warnings)),
    )


def write_project_package(
    package_root: Path,
    project: Project,
    *,
    manifest: dict[str, Any] | None = None,
    overwrite: bool = False,
    compression: ProjectPackageCompression = "none",
) -> ProjectPackage:
    """Write a directory-backed Rietveld project package.

    The writer creates ``project.json`` or deterministic ``project.json.gz``
    and, when supplied, ``manifest.json``. It refuses to overwrite existing
    files unless ``overwrite=True`` is passed. Project JSON is schema-validated
    before any package files are written.

    Args:
        package_root: Package directory to create or update.
        project: Project metadata model to serialize.
        manifest: Optional JSON-object package manifest.
        overwrite: Whether existing package files may be replaced.
        compression: Project metadata compression. Supported values are
            ``"none"`` and ``"gzip"``.

    Returns:
        The package read back through :func:`read_project_package`.

    Raises:
        ProjectPackageError: If the target is unsafe to write, manifest data is
            invalid, or written metadata fails validation.
    """

    root = Path(package_root)
    normalized_compression = _normalize_compression(compression)
    if root.exists() and not root.is_dir():
        raise ProjectPackageError(f"Project package root must be a directory: {root}")
    if manifest is not None and not isinstance(manifest, dict):
        raise ProjectPackageError("Package manifest must be a JSON object when supplied.")

    project_payload = project_to_json(project)
    root.mkdir(parents=True, exist_ok=True)

    project_path = _project_metadata_path(root, normalized_compression)
    alternate_project_path = _alternate_project_metadata_path(root, normalized_compression)
    manifest_path = root / "manifest.json"
    _ensure_can_write(project_path, overwrite)
    _ensure_no_ambiguous_project_metadata(alternate_project_path, overwrite)
    if manifest is not None:
        _ensure_can_write(manifest_path, overwrite)

    _write_project_payload(project_path, project_payload + "\n", normalized_compression)
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

    project_path = root / _PROJECT_JSON
    gzip_project_path = root / _PROJECT_JSON_GZIP
    project_path_is_file = project_path.is_file()
    gzip_project_path_is_file = gzip_project_path.is_file()
    if project_path.exists() and not project_path_is_file:
        issues.append(
            ProjectPackageIntegrityIssue(
                "invalid_project_metadata_path",
                _PROJECT_JSON,
                "Project metadata path is not a file.",
            )
        )
    if gzip_project_path.exists() and not gzip_project_path_is_file:
        issues.append(
            ProjectPackageIntegrityIssue(
                "invalid_project_metadata_path",
                _PROJECT_JSON_GZIP,
                "Compressed project metadata path is not a file.",
            )
        )
    if project_path_is_file and gzip_project_path_is_file:
        issues.append(
            ProjectPackageIntegrityIssue(
                "ambiguous_project_metadata",
                ".",
                "Package must not contain both project.json and project.json.gz.",
            )
        )
    elif not project_path_is_file and not gzip_project_path_is_file:
        issues.append(
            ProjectPackageIntegrityIssue(
                "missing_project_metadata",
                _PROJECT_JSON,
                "Required project metadata file is missing.",
            )
        )
    else:
        project_metadata_path = gzip_project_path if gzip_project_path_is_file else project_path
        compression: ProjectPackageCompression = "gzip" if gzip_project_path_is_file else "none"
        try:
            project_from_json(_read_project_payload(project_metadata_path, compression))
        except Exception as exc:
            issues.append(
                ProjectPackageIntegrityIssue(
                    "invalid_project_metadata",
                    project_metadata_path.name,
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


def _normalize_compression(compression: str) -> ProjectPackageCompression:
    if compression == "none":
        return "none"
    if compression == "gzip":
        return "gzip"
    raise ProjectPackageError(f"Unsupported project package compression: {compression!r}")


def _project_metadata_path(root: Path, compression: ProjectPackageCompression) -> Path:
    return root / (_PROJECT_JSON_GZIP if compression == "gzip" else _PROJECT_JSON)


def _alternate_project_metadata_path(root: Path, compression: ProjectPackageCompression) -> Path:
    return root / (_PROJECT_JSON if compression == "gzip" else _PROJECT_JSON_GZIP)


def _select_project_metadata_path(root: Path) -> tuple[Path, ProjectPackageCompression]:
    project_path = root / _PROJECT_JSON
    gzip_project_path = root / _PROJECT_JSON_GZIP
    if project_path.exists() and not project_path.is_file():
        raise ProjectPackageError(f"Project metadata path is not a file: {project_path}")
    if gzip_project_path.exists() and not gzip_project_path.is_file():
        raise ProjectPackageError(f"Compressed project metadata path is not a file: {gzip_project_path}")
    if project_path.is_file() and gzip_project_path.is_file():
        raise ProjectPackageError(
            f"Project package contains ambiguous metadata files: {project_path} and {gzip_project_path}"
        )
    if gzip_project_path.is_file():
        return gzip_project_path, "gzip"
    if project_path.is_file():
        return project_path, "none"
    raise ProjectPackageError(f"Project package is missing required metadata file: {project_path}")


def _read_project_payload(path: Path, compression: ProjectPackageCompression) -> str:
    if compression == "none":
        return path.read_text(encoding="utf-8")
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return handle.read()


def _write_project_payload(path: Path, payload: str, compression: ProjectPackageCompression) -> None:
    if compression == "none":
        path.write_text(payload, encoding="utf-8")
        return
    with path.open("wb") as raw_handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as gzip_handle:
            gzip_handle.write(payload.encode("utf-8"))


def _ensure_no_ambiguous_project_metadata(path: Path, overwrite: bool) -> None:
    if not path.exists():
        return
    if not overwrite:
        raise ProjectPackageError(
            f"Refusing to create ambiguous package metadata without overwrite=True: {path}"
        )
    if not path.is_file():
        raise ProjectPackageError(f"Project metadata path is not a file: {path}")
    path.unlink()
