"""Small JSON serialization helpers for HPC payload models."""

from __future__ import annotations

import json
import math
from types import MappingProxyType
from typing import Any, Mapping


JSON_SCALAR_TYPES = (str, int, float, bool, type(None))


def immutable_mapping(value: Mapping[str, Any], field_name: str) -> Mapping[str, Any]:
    """Return a shallow immutable copy of a mapping.

    Args:
        value: Mapping to copy.
        field_name: Name used in error messages.

    Returns:
        A read-only mapping copy.

    Raises:
        TypeError: If value is not a mapping.
        ValueError: If keys are not strings or values are not JSON-like.
    """

    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    copied = dict(value)
    validate_json_like(copied, field_name)
    return MappingProxyType(copied)


def stable_json(value: Any) -> str:
    """Serialize a JSON-like value with stable ordering and separators."""

    validate_json_like(value, "value")
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def validate_json_like(value: Any, field_name: str) -> None:
    """Validate that a value can be represented as portable JSON.

    Args:
        value: Candidate JSON-like value.
        field_name: Name used in error messages.

    Raises:
        ValueError: If the value contains non-string mapping keys or unsupported
            object types.
    """

    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{field_name} must be finite")
    if isinstance(value, JSON_SCALAR_TYPES):
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{field_name} mapping keys must be strings")
            validate_json_like(child, f"{field_name}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            validate_json_like(child, f"{field_name}[{index}]")
        return
    raise ValueError(f"{field_name} must be JSON-compatible, got {type(value).__name__}")
