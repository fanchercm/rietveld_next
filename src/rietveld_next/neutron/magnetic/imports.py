"""Magnetic import skeletons with explicit unsupported-field reporting."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import shlex
from typing import Any


SUPPORTED_MCIF_SCALAR_FIELDS = frozenset(
    {
        "_audit_creation_method",
        "_cell_angle_alpha",
        "_cell_angle_beta",
        "_cell_angle_gamma",
        "_cell_length_a",
        "_cell_length_b",
        "_cell_length_c",
        "_magnetic_space_group_bns_number",
        "_magnetic_space_group_name_bns",
        "_magnetic_space_group_name_og",
    }
)


@dataclass(frozen=True)
class MagneticCifImportResult:
    """Deterministic summary from the startup mCIF scalar-field importer.

    Args:
        data_block: CIF data-block name without the ``data_`` prefix.
        supported_fields: Supported scalar mCIF fields found in the payload.
        unsupported_fields: mCIF tags and constructs intentionally not imported.
        warnings: Human-readable import limitations.
        source_format: Import format identifier.
        schema_version: Result schema version for future migration.

    Example:
        >>> result = parse_magnetic_cif_skeleton("data_demo\\n_cell_length_a 5.0")
        >>> result.supported_fields["_cell_length_a"]
        '5.0'
    """

    data_block: str
    supported_fields: dict[str, str] = field(default_factory=dict)
    unsupported_fields: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    source_format: str = "mcif"
    schema_version: str = "m24-mcif-skeleton-v1"

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible import report."""

        return {
            "schema_version": self.schema_version,
            "source_format": self.source_format,
            "data_block": self.data_block,
            "supported_fields": dict(sorted(self.supported_fields.items())),
            "unsupported_fields": list(self.unsupported_fields),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class RepresentationAnalysisImportPlaceholder:
    """Documented placeholder for future representation-analysis imports.

    Args:
        source_tool: Name of the representation-analysis source tool.
        source_version: Optional source-tool version string.
        irrep_labels: Deterministic labels advertised by the source payload.
        basis_vector_count: Number of basis vectors reported by the payload.
        unsupported_reason: Why numerical representation import is not yet run.
        extension_contract: Required fields for a future complete importer.

    Raises:
        ValueError: If labels, counts, or provenance strings are invalid.

    Example:
        >>> placeholder = RepresentationAnalysisImportPlaceholder("BasIreps", None, ("G1",), 2)
        >>> placeholder.status
        'placeholder'
    """

    source_tool: str
    source_version: str | None
    irrep_labels: tuple[str, ...]
    basis_vector_count: int
    unsupported_reason: str = (
        "Representation-analysis import is a metadata placeholder; basis-vector "
        "matrices are not interpreted until a validated source-tool contract is added."
    )
    extension_contract: tuple[str, ...] = (
        "source_tool",
        "source_version",
        "parent_space_group",
        "propagation_vector_rlu",
        "irrep_labels",
        "basis_vectors",
        "site_mapping",
        "normalization_convention",
        "source_provenance",
    )

    def __post_init__(self) -> None:
        """Validate placeholder provenance and declared representation shape."""

        _non_empty_string(self.source_tool, "source_tool")
        if self.source_version is not None:
            _non_empty_string(self.source_version, "source_version")
        if not isinstance(self.basis_vector_count, int) or isinstance(self.basis_vector_count, bool):
            raise ValueError("basis_vector_count must be an integer.")
        if self.basis_vector_count < 0:
            raise ValueError("basis_vector_count must be non-negative.")
        labels = _string_tuple(self.irrep_labels, "irrep_labels")
        contract = _string_tuple(self.extension_contract, "extension_contract")
        object.__setattr__(self, "irrep_labels", labels)
        object.__setattr__(self, "extension_contract", contract)

    @property
    def status(self) -> str:
        """Return the import status marker."""

        return "placeholder"

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible placeholder report."""

        return {
            "status": self.status,
            "source_tool": self.source_tool,
            "source_version": self.source_version,
            "irrep_labels": list(self.irrep_labels),
            "basis_vector_count": self.basis_vector_count,
            "unsupported_reason": self.unsupported_reason,
            "extension_contract": list(self.extension_contract),
        }


def parse_magnetic_cif_skeleton(text: str) -> MagneticCifImportResult:
    """Parse a small, line-oriented subset of mCIF scalar metadata.

    Args:
        text: mCIF text. The skeleton accepts one ``data_`` line and scalar
            tag-value pairs for cell and magnetic-space-group metadata.

    Returns:
        Import report containing supported scalar fields, unsupported tags, and
        warnings for loops or unimplemented constructs.

    Raises:
        ValueError: If ``text`` is empty, has duplicate supported fields, or
            contains malformed scalar lines.

    Example:
        >>> parse_magnetic_cif_skeleton("data_demo\\n_cell_length_a 5.0").data_block
        'demo'
    """

    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty mCIF string.")

    data_block = "unknown"
    supported: dict[str, str] = {}
    unsupported: list[str] = []
    warnings: list[str] = [
        "mCIF import is a scalar-field skeleton; loops, operators, moments, and "
        "basis vectors are reported but not imported."
    ]
    in_loop = False

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        lower = line.lower()
        if lower.startswith("data_"):
            data_block = line[5:] or "unknown"
            in_loop = False
            continue
        if lower == "loop_":
            in_loop = True
            _append_unique(unsupported, "loop_")
            continue
        if not line.startswith("_"):
            if in_loop:
                continue
            raise ValueError(f"mCIF line {line_number} is not a tag-value pair.")

        tokens = shlex.split(line, comments=False, posix=True)
        if len(tokens) < 1:
            continue
        tag = tokens[0].lower()
        if in_loop and len(tokens) == 1:
            _append_unique(unsupported, tag)
            continue
        if len(tokens) < 2:
            raise ValueError(f"mCIF field {tokens[0]!r} on line {line_number} is missing a value.")
        value = " ".join(tokens[1:])
        if tag in SUPPORTED_MCIF_SCALAR_FIELDS:
            if tag in supported:
                raise ValueError(f"mCIF field {tag!r} is duplicated.")
            _validate_supported_mcif_value(tag, value)
            supported[tag] = value
        else:
            _append_unique(unsupported, tag)

    return MagneticCifImportResult(
        data_block=data_block,
        supported_fields=dict(sorted(supported.items())),
        unsupported_fields=tuple(unsupported),
        warnings=tuple(warnings),
    )


def create_representation_analysis_placeholder(
    payload: Mapping[str, Any],
) -> RepresentationAnalysisImportPlaceholder:
    """Create a representation-analysis placeholder from source metadata.

    Args:
        payload: Mapping with ``source_tool``, optional ``source_version``,
            optional ``irrep_labels``, and optional ``basis_vector_count``.

    Returns:
        Structured placeholder documenting the future importer contract.

    Raises:
        ValueError: If required provenance or declared counts are invalid.

    Example:
        >>> create_representation_analysis_placeholder({"source_tool": "BasIreps"}).basis_vector_count
        0
    """

    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping.")
    if "source_tool" not in payload:
        raise ValueError("payload is missing required key: source_tool.")
    labels = payload.get("irrep_labels", ())
    if isinstance(labels, str):
        raise ValueError("irrep_labels must be a sequence of strings, not a string.")
    return RepresentationAnalysisImportPlaceholder(
        source_tool=payload["source_tool"],
        source_version=payload.get("source_version"),
        irrep_labels=tuple(labels),
        basis_vector_count=payload.get("basis_vector_count", 0),
    )


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _validate_supported_mcif_value(tag: str, value: str) -> None:
    if tag.startswith("_cell_length_"):
        length = _finite_float(value, tag)
        if length <= 0.0:
            raise ValueError(f"{tag} must be positive in angstroms.")
    elif tag.startswith("_cell_angle_"):
        angle = _finite_float(value, tag)
        if angle <= 0.0 or angle >= 180.0:
            raise ValueError(f"{tag} must be greater than 0 and less than 180 degrees.")
    else:
        _non_empty_string(value, tag)


def _finite_float(value: str, name: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a finite numeric value.") from exc
    if number != number or number in (float("inf"), float("-inf")):
        raise ValueError(f"{name} must be a finite numeric value.")
    return number


def _non_empty_string(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value


def _string_tuple(values: Sequence[str], name: str) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of strings.")
    normalized = []
    for index, value in enumerate(values):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name}[{index}] must be a non-empty string.")
        normalized.append(value)
    return tuple(normalized)
