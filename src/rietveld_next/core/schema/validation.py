"""JSON Schema validation and schema-backed project serialization.

This module intentionally implements only the JSON Schema keywords used by
``schemas/project.schema.json``. It gives the project deterministic validation
without introducing an external runtime dependency before workspace build
conventions are finalized.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import math
from pathlib import Path
import re
from typing import Any

from rietveld_next.core.model import Project
from rietveld_next.core.model.errors import ModelValidationError


@dataclass(frozen=True)
class SchemaValidationIssue:
    """Single JSON Schema validation issue.

    Args:
        path: Dot/bracket path to the failing value.
        message: Human-readable validation message.
        keyword: JSON Schema keyword that produced the issue.
    """

    path: str
    message: str
    keyword: str


class SchemaValidationError(ValueError):
    """Raised when project metadata fails JSON Schema validation.

    Args:
        issues: Validation issues in deterministic traversal order.
    """

    def __init__(self, issues: list[SchemaValidationIssue]) -> None:
        if not issues:
            raise ValueError("SchemaValidationError requires at least one issue.")
        self.issues = issues
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        first = self.issues[0]
        suffix = "" if len(self.issues) == 1 else f" ({len(self.issues)} total issues)"
        return f"{first.path}: {first.message}{suffix}"


def load_project_schema(schema_path: Path | None = None) -> dict[str, Any]:
    """Load the canonical project JSON Schema.

    Args:
        schema_path: Optional explicit schema path. When omitted, the repository
            ``schemas/project.schema.json`` file is loaded relative to this
            source file.

    Returns:
        Parsed schema mapping.

    Raises:
        ModelValidationError: If the schema file cannot be decoded as an
            object.
    """
    path = schema_path or Path(__file__).resolve().parents[4] / "schemas" / "project.schema.json"
    with path.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    if not isinstance(schema, dict):
        raise ModelValidationError("invalid_schema", "Project schema file must contain a JSON object.", str(path))
    return schema


def validate_project_mapping(data: dict[str, Any], schema: dict[str, Any] | None = None) -> None:
    """Validate project metadata against the canonical JSON Schema.

    Args:
        data: Project metadata mapping.
        schema: Optional schema mapping. Defaults to
            ``schemas/project.schema.json``.

    Raises:
        SchemaValidationError: If ``data`` fails schema validation.
    """
    active_schema = schema or load_project_schema()
    issues: list[SchemaValidationIssue] = []
    _validate_node(data, active_schema, active_schema, "$", issues)
    if issues:
        raise SchemaValidationError(issues)


def validate_project_json(payload: str, schema: dict[str, Any] | None = None) -> dict[str, Any]:
    """Decode and validate project metadata JSON.

    Args:
        payload: Serialized project metadata.
        schema: Optional schema mapping.

    Returns:
        Decoded project mapping.

    Raises:
        SchemaValidationError: If JSON decoding or schema validation fails.
    """
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        issue = SchemaValidationIssue("$", f"Invalid JSON: {exc.msg}.", "json")
        raise SchemaValidationError([issue]) from exc
    if not isinstance(data, dict):
        raise SchemaValidationError([SchemaValidationIssue("$", "Project payload must be a JSON object.", "type")])
    validate_project_mapping(data, schema)
    return data


def project_to_json(project: Project, schema: dict[str, Any] | None = None) -> str:
    """Serialize a project and validate the emitted metadata.

    Args:
        project: Project model to serialize.
        schema: Optional schema mapping.

    Returns:
        Deterministic JSON text.

    Raises:
        SchemaValidationError: If the emitted metadata does not satisfy the
            project schema.
    """
    data = project.to_schema_dict()
    validate_project_mapping(data, schema)
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def project_from_json(payload: str, schema: dict[str, Any] | None = None) -> Project:
    """Validate and deserialize project metadata.

    Args:
        payload: Serialized project metadata.
        schema: Optional schema mapping.

    Returns:
        Project model instance.

    Raises:
        SchemaValidationError: If JSON Schema validation fails.
        ModelValidationError: If model graph validation fails after schema
            validation.
    """
    return Project.from_dict(validate_project_json(payload, schema))


def _validate_node(
    value: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
    issues: list[SchemaValidationIssue],
) -> None:
    if "$ref" in schema:
        _validate_node(value, _resolve_ref(schema["$ref"], root_schema), root_schema, path, issues)
        return

    if "type" in schema and not _matches_type(value, schema["type"]):
        expected = schema["type"]
        issues.append(SchemaValidationIssue(path, f"Expected type {expected!r}.", "type"))
        return

    if "enum" in schema and value not in schema["enum"]:
        issues.append(SchemaValidationIssue(path, f"Expected one of {schema['enum']!r}.", "enum"))

    if isinstance(value, str) and "pattern" in schema:
        pattern = schema["pattern"]
        if re.search(pattern, value) is None:
            issues.append(SchemaValidationIssue(path, f"String does not match pattern {pattern!r}.", "pattern"))

    if isinstance(value, str) and "minLength" in schema and len(value) < schema["minLength"]:
        issues.append(SchemaValidationIssue(path, f"Expected at least {schema['minLength']} characters.", "minLength"))

    if isinstance(value, str) and schema.get("format") == "date-time":
        if not _is_datetime(value):
            issues.append(SchemaValidationIssue(path, "Expected an RFC 3339-like date-time string.", "format"))

    if isinstance(value, int | float) and not isinstance(value, bool):
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            issues.append(
                SchemaValidationIssue(
                    path,
                    f"Expected a value greater than {schema['exclusiveMinimum']!r}.",
                    "exclusiveMinimum",
                )
            )
        if "minimum" in schema and value < schema["minimum"]:
            issues.append(SchemaValidationIssue(path, f"Expected a value at least {schema['minimum']!r}.", "minimum"))

    if isinstance(value, dict):
        _validate_object(value, schema, root_schema, path, issues)
    elif isinstance(value, list):
        _validate_array(value, schema, root_schema, path, issues)


def _validate_object(
    value: dict[str, Any],
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
    issues: list[SchemaValidationIssue],
) -> None:
    required = schema.get("required", [])
    for field_name in required:
        if field_name not in value:
            issues.append(SchemaValidationIssue(path, f"Missing required property {field_name!r}.", "required"))

    properties = schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name in sorted(properties):
            if field_name in value:
                _validate_node(value[field_name], properties[field_name], root_schema, f"{path}.{field_name}", issues)

    additional = schema.get("additionalProperties", True)
    if additional is not True and isinstance(properties, dict):
        known_properties = set(properties)
        for field_name in sorted(set(value) - known_properties):
            if additional is False:
                issues.append(
                    SchemaValidationIssue(
                        f"{path}.{field_name}",
                        "Additional properties are not allowed.",
                        "additionalProperties",
                    )
                )
            elif isinstance(additional, dict):
                _validate_node(value[field_name], additional, root_schema, f"{path}.{field_name}", issues)


def _validate_array(
    value: list[Any],
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
    issues: list[SchemaValidationIssue],
) -> None:
    if "minItems" in schema and len(value) < schema["minItems"]:
        issues.append(SchemaValidationIssue(path, f"Expected at least {schema['minItems']} items.", "minItems"))
    if "maxItems" in schema and len(value) > schema["maxItems"]:
        issues.append(SchemaValidationIssue(path, f"Expected at most {schema['maxItems']} items.", "maxItems"))

    item_schema = schema.get("items")
    if isinstance(item_schema, dict):
        for index, item in enumerate(value):
            _validate_node(item, item_schema, root_schema, f"{path}[{index}]", issues)


def _resolve_ref(ref: str, root_schema: dict[str, Any]) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ModelValidationError("unsupported_schema_ref", "Only local schema refs are supported.", ref)
    node: Any = root_schema
    for part in ref[2:].split("/"):
        if not isinstance(node, dict) or part not in node:
            raise ModelValidationError("invalid_schema_ref", "Schema ref could not be resolved.", ref)
        node = node[part]
    if not isinstance(node, dict):
        raise ModelValidationError("invalid_schema_ref", "Schema ref must resolve to an object.", ref)
    return node


def _matches_type(value: Any, expected: str | list[str]) -> bool:
    expected_types = [expected] if isinstance(expected, str) else expected
    return any(_matches_single_type(value, item) for item in expected_types)


def _matches_single_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ModelValidationError("unsupported_schema_type", "Unsupported JSON Schema type.", expected)


def _is_datetime(value: str) -> bool:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return True
