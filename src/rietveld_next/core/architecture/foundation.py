"""Foundation metadata primitives for repository architecture work.

This module provides small, dependency-free helpers for M01 architecture
foundation tasks. The helpers are metadata and workflow utilities only; they do
not implement scientific calculations.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping


IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]*$")
SCHEMA_VERSION = "1.0.0"


class ArchitectureErrorCode(StrEnum):
    """Stable error codes for architecture foundation helpers."""

    INVALID_CONFIGURATION = "invalid_configuration"
    CONFIGURATION_NOT_FOUND = "configuration_not_found"
    UNSUPPORTED_CONFIGURATION_FORMAT = "unsupported_configuration_format"
    INVALID_FEATURE_FLAG = "invalid_feature_flag"
    INVALID_PROVENANCE_EVENT = "invalid_provenance_event"
    INVALID_RELEASE_MANIFEST = "invalid_release_manifest"
    INVALID_ARTIFACT = "invalid_artifact"


class ApiStability(StrEnum):
    """Public API stability levels for M01 architecture documentation."""

    INTERNAL = "internal"
    EXPERIMENTAL = "experimental"
    PROVISIONAL = "provisional"
    STABLE = "stable"
    DEPRECATED = "deprecated"


class ArchitectureError(ValueError):
    """Structured architecture foundation error.

    Args:
        code: Stable error code.
        message: Human-readable explanation.
        path: Optional configuration, field, or artifact path.
        details: Optional deterministic metadata for diagnostics.
    """

    def __init__(
        self,
        code: ArchitectureErrorCode,
        message: str,
        path: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.path = path
        self.details = dict(details or {})
        prefix = f"{code.value}: "
        suffix = f" ({path})" if path else ""
        super().__init__(f"{prefix}{message}{suffix}")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible representation."""

        return {
            "code": self.code.value,
            "details": dict(sorted(self.details.items())),
            "message": str(self),
            "path": self.path,
        }


@dataclass(frozen=True)
class FeatureFlag:
    """Feature flag metadata with deterministic defaults.

    Args:
        name: Stable feature flag identifier.
        description: Short developer-facing purpose.
        default_enabled: Whether the feature is enabled without overrides.
        stability: Public API stability level for the feature.
        owner: Optional owning package or workstream.
    """

    name: str
    description: str
    default_enabled: bool = False
    stability: ApiStability = ApiStability.EXPERIMENTAL
    owner: str | None = None

    def __post_init__(self) -> None:
        """Validate flag metadata."""

        _validate_identifier(self.name, "feature_flag.name", ArchitectureErrorCode.INVALID_FEATURE_FLAG)
        if not self.description:
            raise ArchitectureError(
                ArchitectureErrorCode.INVALID_FEATURE_FLAG,
                "Feature flag description must be non-empty.",
                "feature_flag.description",
            )
        if self.owner is not None:
            _validate_identifier(self.owner, "feature_flag.owner", ArchitectureErrorCode.INVALID_FEATURE_FLAG)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible representation."""

        return {
            "default_enabled": self.default_enabled,
            "description": self.description,
            "name": self.name,
            "owner": self.owner,
            "stability": self.stability.value,
        }


@dataclass(frozen=True)
class FeatureFlagRegistry:
    """Immutable collection of feature flag metadata."""

    flags: tuple[FeatureFlag, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate unique feature flag names."""

        names = [flag.name for flag in self.flags]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ArchitectureError(
                ArchitectureErrorCode.INVALID_FEATURE_FLAG,
                "Feature flag names must be unique.",
                "feature_flags",
                {"duplicates": duplicates},
            )

    def is_enabled(self, name: str, overrides: Mapping[str, bool] | None = None) -> bool:
        """Return the effective enabled state for a feature flag.

        Args:
            name: Feature flag name.
            overrides: Optional explicit flag states.

        Raises:
            ArchitectureError: If ``name`` is not registered or an override is
                not boolean.
        """

        flag_map = {flag.name: flag for flag in self.flags}
        if name not in flag_map:
            raise ArchitectureError(
                ArchitectureErrorCode.INVALID_FEATURE_FLAG,
                "Feature flag is not registered.",
                name,
            )
        if overrides and name in overrides:
            value = overrides[name]
            if not isinstance(value, bool):
                raise ArchitectureError(
                    ArchitectureErrorCode.INVALID_FEATURE_FLAG,
                    "Feature flag override must be boolean.",
                    name,
                    {"value": value},
                )
            return value
        return flag_map[name].default_enabled

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic registry metadata."""

        return {"flags": [flag.to_dict() for flag in sorted(self.flags, key=lambda item: item.name)]}


@dataclass(frozen=True)
class ProvenanceEvent:
    """Append-only event envelope for reproducible architecture workflows."""

    event_id: str
    actor: str
    action: str
    timestamp_utc: str
    subject: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate event identity, action, and timestamp."""

        _validate_identifier(self.event_id, "provenance.event_id", ArchitectureErrorCode.INVALID_PROVENANCE_EVENT)
        if not self.actor:
            raise ArchitectureError(ArchitectureErrorCode.INVALID_PROVENANCE_EVENT, "Actor must be non-empty.", "actor")
        if not self.action:
            raise ArchitectureError(ArchitectureErrorCode.INVALID_PROVENANCE_EVENT, "Action must be non-empty.", "action")
        _parse_utc_timestamp(self.timestamp_utc)
        object.__setattr__(self, "details", _freeze_mapping(self.details))

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic event metadata."""

        return {
            "action": self.action,
            "actor": self.actor,
            "details": _canonical_mapping(_thaw_value(self.details)),
            "event_id": self.event_id,
            "schema_version": self.schema_version,
            "subject": self.subject,
            "timestamp_utc": self.timestamp_utc,
        }


def create_provenance_event(
    *,
    actor: str,
    action: str,
    timestamp_utc: str,
    subject: str | None = None,
    details: Mapping[str, Any] | None = None,
    event_id: str | None = None,
) -> ProvenanceEvent:
    """Create a deterministic provenance event envelope.

    Args:
        actor: User, service, or tool responsible for the action.
        action: Stable action name.
        timestamp_utc: RFC 3339-like UTC timestamp ending in ``Z``.
        subject: Optional artifact or entity affected by the event.
        details: Optional JSON-compatible metadata.
        event_id: Optional explicit event ID. When omitted, an ID is derived
            from the canonical event fields.

    Returns:
        Validated provenance event.
    """

    payload = {
        "action": action,
        "actor": actor,
        "details": _canonical_mapping(dict(details or {})),
        "schema_version": SCHEMA_VERSION,
        "subject": subject,
        "timestamp_utc": timestamp_utc,
    }
    resolved_event_id = event_id or f"evt_{_stable_digest(payload)[:16]}"
    return ProvenanceEvent(
        event_id=resolved_event_id,
        actor=actor,
        action=action,
        timestamp_utc=timestamp_utc,
        subject=subject,
        details=dict(details or {}),
    )


@dataclass(frozen=True)
class EnvironmentSnapshot:
    """Small reproducibility snapshot for local execution context."""

    python_version: str
    platform: str
    executable: str
    environment_variables: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic environment metadata."""

        return {
            "environment_variables": dict(sorted(self.environment_variables.items())),
            "executable": self.executable,
            "platform": self.platform,
            "python_version": self.python_version,
        }


def capture_environment(variable_names: Iterable[str] = ()) -> EnvironmentSnapshot:
    """Capture lightweight environment metadata.

    Args:
        variable_names: Environment variable names to include. Variables that
            are absent are omitted; no full environment dump is taken.

    Returns:
        Reproducibility-oriented environment snapshot.
    """

    selected = {name: os.environ[name] for name in sorted(set(variable_names)) if name in os.environ}
    return EnvironmentSnapshot(
        python_version=sys.version.split()[0],
        platform=platform.platform(),
        executable=sys.executable,
        environment_variables=selected,
    )


def load_configuration(
    paths: Iterable[Path],
    *,
    defaults: Mapping[str, Any] | None = None,
    overrides: Mapping[str, Any] | None = None,
    require_existing: bool = False,
) -> dict[str, Any]:
    """Load and merge JSON configuration files deterministically.

    Args:
        paths: JSON object files to merge from left to right.
        defaults: Base configuration values.
        overrides: Final configuration values.
        require_existing: Whether missing paths should fail.

    Returns:
        Merged JSON-compatible configuration mapping.

    Raises:
        ArchitectureError: If a path is missing when required, has an
            unsupported extension, or does not decode to a JSON object.
    """

    merged: dict[str, Any] = _canonical_mapping(dict(defaults or {}))
    for path in paths:
        if not path.exists():
            if require_existing:
                raise ArchitectureError(
                    ArchitectureErrorCode.CONFIGURATION_NOT_FOUND,
                    "Configuration file does not exist.",
                    str(path),
                )
            continue
        if path.suffix.lower() != ".json":
            raise ArchitectureError(
                ArchitectureErrorCode.UNSUPPORTED_CONFIGURATION_FORMAT,
                "Only JSON configuration files are supported.",
                str(path),
            )
        try:
            with path.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ArchitectureError(
                ArchitectureErrorCode.INVALID_CONFIGURATION,
                "Configuration file is not valid JSON.",
                str(path),
                {"line": exc.lineno},
            ) from exc
        if not isinstance(loaded, dict):
            raise ArchitectureError(
                ArchitectureErrorCode.INVALID_CONFIGURATION,
                "Configuration file must contain a JSON object.",
                str(path),
            )
        merged = _merge_mappings(merged, loaded)
    return _merge_mappings(merged, dict(overrides or {}))


@dataclass(frozen=True)
class ReleaseArtifact:
    """Single release artifact manifest entry."""

    path: str
    sha256: str
    size_bytes: int
    kind: str

    def __post_init__(self) -> None:
        """Validate artifact metadata."""

        if not self.path or Path(self.path).is_absolute() or ".." in Path(self.path).parts:
            raise ArchitectureError(
                ArchitectureErrorCode.INVALID_ARTIFACT,
                "Artifact path must be a non-empty relative path inside the repository.",
                self.path,
            )
        if not re.fullmatch(r"[0-9a-f]{64}", self.sha256):
            raise ArchitectureError(
                ArchitectureErrorCode.INVALID_ARTIFACT,
                "Artifact sha256 must be lowercase hexadecimal.",
                self.path,
            )
        if self.size_bytes < 0:
            raise ArchitectureError(
                ArchitectureErrorCode.INVALID_ARTIFACT,
                "Artifact size cannot be negative.",
                self.path,
            )
        _validate_identifier(self.kind, "artifact.kind", ArchitectureErrorCode.INVALID_ARTIFACT)

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic artifact metadata."""

        return {
            "kind": self.kind,
            "path": self.path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class ReleaseManifest:
    """Deterministic release artifact manifest."""

    version: str
    artifacts: tuple[ReleaseArtifact, ...]
    created_at_utc: str
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate release manifest metadata."""

        if not self.version:
            raise ArchitectureError(ArchitectureErrorCode.INVALID_RELEASE_MANIFEST, "Version must be non-empty.", "version")
        _parse_utc_timestamp(
            self.created_at_utc,
            code=ArchitectureErrorCode.INVALID_RELEASE_MANIFEST,
            path="created_at_utc",
        )
        paths = [artifact.path for artifact in self.artifacts]
        duplicates = sorted({path for path in paths if paths.count(path) > 1})
        if duplicates:
            raise ArchitectureError(
                ArchitectureErrorCode.INVALID_RELEASE_MANIFEST,
                "Artifact paths must be unique.",
                "artifacts",
                {"duplicates": duplicates},
            )

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic manifest metadata."""

        return {
            "artifacts": [artifact.to_dict() for artifact in sorted(self.artifacts, key=lambda item: item.path)],
            "created_at_utc": self.created_at_utc,
            "schema_version": self.schema_version,
            "version": self.version,
        }


def build_release_manifest(
    *,
    root: Path,
    artifact_paths: Iterable[Path],
    version: str,
    created_at_utc: str,
    kind: str = "release_artifact",
) -> ReleaseManifest:
    """Build a release manifest from existing files.

    Args:
        root: Repository root used for relative artifact paths.
        artifact_paths: Files to include in the manifest.
        version: Release version label.
        created_at_utc: RFC 3339-like UTC timestamp ending in ``Z``.
        kind: Artifact kind label.

    Returns:
        Deterministic release manifest.

    Raises:
        ArchitectureError: If any artifact is outside ``root`` or missing.
    """

    resolved_root = root.resolve()
    artifacts: list[ReleaseArtifact] = []
    for artifact_path in sorted((path.resolve() for path in artifact_paths), key=str):
        if not artifact_path.is_file():
            raise ArchitectureError(
                ArchitectureErrorCode.INVALID_ARTIFACT,
                "Release artifact does not exist or is not a file.",
                str(artifact_path),
            )
        try:
            relative_path = artifact_path.relative_to(resolved_root)
        except ValueError as exc:
            raise ArchitectureError(
                ArchitectureErrorCode.INVALID_ARTIFACT,
                "Release artifact must be inside the repository root.",
                str(artifact_path),
            ) from exc
        data = artifact_path.read_bytes()
        artifacts.append(
            ReleaseArtifact(
                path=relative_path.as_posix(),
                sha256=hashlib.sha256(data).hexdigest(),
                size_bytes=len(data),
                kind=kind,
            )
        )
    return ReleaseManifest(version=version, artifacts=tuple(artifacts), created_at_utc=created_at_utc)


def _validate_identifier(value: str, path: str, code: ArchitectureErrorCode) -> None:
    if not isinstance(value, str) or IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ArchitectureError(code, "Value must be a stable identifier.", path, {"value": value})


def _parse_utc_timestamp(
    value: str,
    *,
    code: ArchitectureErrorCode = ArchitectureErrorCode.INVALID_PROVENANCE_EVENT,
    path: str = "timestamp_utc",
) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ArchitectureError(
            code,
            "Timestamp must be an RFC 3339-like UTC string ending in Z.",
            path,
            {"value": value},
        )
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ArchitectureError(
            code,
            "Timestamp must be parseable as an RFC 3339-like UTC string.",
            path,
            {"value": value},
        ) from exc


def _merge_mappings(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = _canonical_mapping(dict(left))
    for key in sorted(right):
        right_value = right[key]
        left_value = merged.get(key)
        if isinstance(left_value, dict) and isinstance(right_value, Mapping):
            merged[key] = _merge_mappings(left_value, right_value)
        else:
            merged[key] = _canonical_value(right_value)
    return merged


def _canonical_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
    return {key: _canonical_value(mapping[key]) for key in sorted(mapping)}


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _canonical_mapping(value)
    if isinstance(value, list):
        return [_canonical_value(item) for item in value]
    if isinstance(value, tuple):
        return [_canonical_value(item) for item in value]
    return value


def _freeze_mapping(mapping: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType({key: _freeze_value(mapping[key]) for key in sorted(mapping)})


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _freeze_mapping(value)
    if isinstance(value, list | tuple):
        return tuple(_freeze_value(item) for item in value)
    return value


def _thaw_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_value(value[key]) for key in sorted(value)}
    if isinstance(value, tuple):
        return [_thaw_value(item) for item in value]
    if isinstance(value, list):
        return [_thaw_value(item) for item in value]
    return value


def _stable_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(_canonical_mapping(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
