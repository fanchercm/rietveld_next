"""Project metadata schema migration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
import re
from typing import Any

from rietveld_next.core.model.errors import ModelValidationError

CURRENT_PROJECT_SCHEMA_VERSION = "1.0.0"
_COMPATIBLE_VERSION_PATTERN = re.compile(r"^1\.0\.[0-9]+$")


@dataclass(frozen=True)
class ProjectMigrationStep:
    """Single project metadata migration step.

    Args:
        source_version: Schema version accepted as input.
        target_version: Schema version emitted by the step.
        description: Human-readable migration description.
    """

    source_version: str
    target_version: str
    description: str


@dataclass(frozen=True)
class ProjectMigrationPlan:
    """Deterministic plan for migrating project metadata.

    Args:
        source_version: Input project schema version.
        target_version: Desired output schema version.
        steps: Ordered migration steps. Empty steps mean the payload is already
            on a compatible schema line.
    """

    source_version: str
    target_version: str
    steps: tuple[ProjectMigrationStep, ...] = ()

    @property
    def requires_changes(self) -> bool:
        """Return whether the plan will mutate payload content."""
        return bool(self.steps)


def plan_project_migration(
    source_version: str,
    target_version: str = CURRENT_PROJECT_SCHEMA_VERSION,
) -> ProjectMigrationPlan:
    """Build a deterministic migration plan for project metadata.

    The initial M02 schema supports the `1.0.x` compatibility line only. Patch
    versions in that line are compatible and currently require no structural
    edits; unsupported major or minor versions fail with a structured model
    validation error.

    Args:
        source_version: Schema version in the input payload.
        target_version: Desired schema version. Defaults to the current M02
            project schema version.

    Returns:
        Migration plan from source to target.

    Raises:
        ModelValidationError: If either version is outside the supported
            `1.0.x` compatibility line.
    """
    _validate_supported_version(source_version, "source_version")
    _validate_supported_version(target_version, "target_version")
    if source_version == target_version:
        return ProjectMigrationPlan(source_version=source_version, target_version=target_version)
    return ProjectMigrationPlan(
        source_version=source_version,
        target_version=target_version,
        steps=(
            ProjectMigrationStep(
                source_version=source_version,
                target_version=target_version,
                description="Normalize project metadata schema_version within the 1.0.x compatibility line.",
            ),
        ),
    )


def migrate_project_mapping(
    data: dict[str, Any],
    target_version: str = CURRENT_PROJECT_SCHEMA_VERSION,
) -> dict[str, Any]:
    """Migrate a project metadata mapping to a target schema version.

    Args:
        data: Project metadata mapping. The input mapping is not mutated.
        target_version: Desired output schema version.

    Returns:
        Deep-copied project metadata with a normalized `schema_version`.

    Raises:
        ModelValidationError: If the payload is not a mapping, omits
            `schema_version`, or uses an unsupported schema line.
    """
    if not isinstance(data, dict):
        raise ModelValidationError("invalid_payload", "Project migration input must be an object.", "project")
    source_version = data.get("schema_version")
    if not isinstance(source_version, str):
        raise ModelValidationError(
            "missing_schema_version",
            "Project migration input must include a string schema_version.",
            "project.schema_version",
        )
    plan_project_migration(source_version, target_version)
    migrated = deepcopy(data)
    migrated["schema_version"] = target_version
    return migrated


def _validate_supported_version(version: str, path: str) -> None:
    if not isinstance(version, str) or _COMPATIBLE_VERSION_PATTERN.fullmatch(version) is None:
        raise ModelValidationError(
            "unsupported_schema_version",
            "Project migrations currently support only the 1.0.x schema compatibility line.",
            path,
            {"value": version},
        )
