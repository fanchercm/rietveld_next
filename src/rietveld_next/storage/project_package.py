"""Read-only Rietveld project package loader."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from rietveld_next.core.model import Project
from rietveld_next.core.schema import project_from_json


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
