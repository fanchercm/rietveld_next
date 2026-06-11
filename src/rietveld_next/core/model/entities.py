"""Typed scientific domain entities for Rietveld Next.

The objects in this module define the project metadata graph only. They do not
load profile arrays, run numerical kernels, call storage backends, or implement
UI/AI behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import json
import math
import re
from typing import Any, ClassVar, TypeVar, get_args, get_origin, get_type_hints

from rietveld_next.core.model.errors import ModelValidationError

ENTITY_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]*$")
PATH_SEGMENT_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]*$")
SCHEMA_VERSION_PATTERN = re.compile(r"^1\.0\.[0-9]+$")

T = TypeVar("T")


class StrValueEnum(str, Enum):
    """Enum that serializes to its string value."""


class RadiationType(StrValueEnum):
    """Supported experiment radiation families."""

    LAB_XRAY_CW = "lab_xray_cw"
    SYNCHROTRON_XRAY_CW = "synchrotron_xray_cw"
    SYNCHROTRON_XRAY_EDXRD = "synchrotron_xray_edxrd"
    NEUTRON_CW = "neutron_cw"
    NEUTRON_TOF = "neutron_tof"


class AxisType(StrValueEnum):
    """Supported histogram axis coordinates."""

    TWO_THETA = "two_theta"
    TOF = "tof"
    ENERGY = "energy"
    D_SPACING = "d_spacing"
    Q = "q"


class ConstraintKind(StrValueEnum):
    """Supported constraint relation classes."""

    EQUALITY = "equality"
    INEQUALITY = "inequality"
    LINEAR = "linear"
    SYMBOLIC = "symbolic"
    RESTRAINT = "restraint"


class OptimizationMethod(StrValueEnum):
    """Named optimizer strategy families."""

    LEAST_SQUARES = "least_squares"
    ROBUST_LEAST_SQUARES = "robust_least_squares"
    POISSON_LIKELIHOOD = "poisson_likelihood"
    GLOBAL_SEARCH = "global_search"


def validate_entity_id(entity_id: str, path: str) -> None:
    """Validate an entity identifier.

    Args:
        entity_id: Identifier to validate.
        path: Model path used in error reports.

    Raises:
        ModelValidationError: If the ID is empty or contains unsupported
            characters.
    """
    if not isinstance(entity_id, str) or not entity_id:
        raise ModelValidationError("invalid_id", "Entity ID must be a non-empty string.", path)
    if ENTITY_ID_PATTERN.fullmatch(entity_id) is None:
        raise ModelValidationError(
            "invalid_id",
            "Entity ID must start with a letter and contain only letters, digits, '_', '.', ':', or '-'.",
            path,
            {"value": entity_id},
        )


def _require_mapping(data: Any, cls_name: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ModelValidationError("invalid_payload", f"{cls_name} payload must be an object.")
    return data


def _require_fields(data: dict[str, Any], required: tuple[str, ...], cls_name: str) -> None:
    missing = [name for name in required if name not in data]
    if missing:
        raise ModelValidationError(
            "missing_required_field",
            f"{cls_name} is missing required field(s): {', '.join(missing)}.",
            cls_name,
            {"missing": missing},
        )


def _finite_number(value: float, path: str) -> None:
    if not isinstance(value, int | float) or isinstance(value, bool) or not math.isfinite(value):
        raise ModelValidationError("invalid_number", "Value must be a finite number.", path, {"value": value})


def _enum_value(enum_type: type[StrValueEnum], value: Any, path: str) -> StrValueEnum:
    try:
        return enum_type(value)
    except ValueError as exc:
        allowed = [item.value for item in enum_type]
        raise ModelValidationError(
            "invalid_enum",
            f"Value must be one of: {', '.join(allowed)}.",
            path,
            {"value": value, "allowed": allowed},
        ) from exc


def _serialize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, ParameterPath):
        return str(value)
    if is_dataclass(value):
        result: dict[str, Any] = {}
        for field_info in fields(value):
            field_value = getattr(value, field_info.name)
            if field_value is None:
                continue
            result[field_info.name] = _serialize(field_value)
        return result
    if isinstance(value, list | tuple):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _serialize(value[key]) for key in sorted(value)}
    return value


def _load_dataclass(cls: type[T], data: Any, required: tuple[str, ...]) -> T:
    mapping = _require_mapping(data, cls.__name__)
    _require_fields(mapping, required, cls.__name__)
    type_hints = get_type_hints(cls)
    kwargs: dict[str, Any] = {}
    for field_info in fields(cls):
        if field_info.name in mapping:
            kwargs[field_info.name] = _coerce_value(type_hints[field_info.name], mapping[field_info.name], field_info.name)
    return cls(**kwargs)


def _coerce_value(type_hint: Any, value: Any, path: str) -> Any:
    origin = get_origin(type_hint)
    args = get_args(type_hint)
    if type_hint is Any:
        return value
    if origin is list:
        if not isinstance(value, list):
            raise ModelValidationError("invalid_type", "Expected a list.", path, {"value": value})
        return [_coerce_value(args[0], item, path) for item in value]
    if origin is dict:
        if not isinstance(value, dict):
            raise ModelValidationError("invalid_type", "Expected an object.", path, {"value": value})
        return dict(value)
    if origin is type(None):
        return None
    if origin is not None and type(None) in args:
        if value is None:
            return None
        non_none = [arg for arg in args if arg is not type(None)][0]
        return _coerce_value(non_none, value, path)
    if type_hint is str:
        if not isinstance(value, str):
            raise ModelValidationError("invalid_type", "Expected a string.", path, {"value": value})
        return value
    if type_hint is bool:
        if not isinstance(value, bool):
            raise ModelValidationError("invalid_type", "Expected a boolean.", path, {"value": value})
        return value
    if type_hint is float:
        if not isinstance(value, int | float) or isinstance(value, bool):
            raise ModelValidationError("invalid_type", "Expected a number.", path, {"value": value})
        return float(value)
    if type_hint is int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise ModelValidationError("invalid_type", "Expected an integer.", path, {"value": value})
        return value
    if isinstance(type_hint, type) and isinstance(value, type_hint):
        return value
    if isinstance(type_hint, type) and issubclass(type_hint, StrValueEnum):
        return _enum_value(type_hint, value, path)
    if type_hint is ParameterPath:
        return ParameterPath.parse(value)
    if isinstance(type_hint, type) and is_dataclass(type_hint):
        return type_hint.from_dict(value)
    return value


@dataclass(frozen=True)
class ParameterPath:
    """Stable address for a refinable model value.

    Args:
        owner_type: Entity family that owns the parameter, such as ``phase``.
        owner_id: Stable ID of the owning entity.
        segments: Path segments below the owner.

    Example:
        >>> str(ParameterPath("phase", "alpha", ("crystal_structure", "cell", "a")))
        'phase/alpha/crystal_structure/cell/a'
    """

    owner_type: str
    owner_id: str
    segments: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate owner and segment syntax."""
        if not self.segments:
            raise ModelValidationError("invalid_parameter_path", "Parameter path requires at least one field segment.")
        for name, value in (("owner_type", self.owner_type), ("owner_id", self.owner_id)):
            if PATH_SEGMENT_PATTERN.fullmatch(value) is None:
                raise ModelValidationError(
                    "invalid_parameter_path",
                    f"{name} must be a stable path segment.",
                    "parameter_path",
                    {"value": value},
                )
        for segment in self.segments:
            if PATH_SEGMENT_PATTERN.fullmatch(segment) is None:
                raise ModelValidationError(
                    "invalid_parameter_path",
                    "All parameter path segments must be stable identifiers.",
                    "parameter_path",
                    {"value": segment},
                )

    @classmethod
    def parse(cls, value: str) -> ParameterPath:
        """Parse a serialized parameter path.

        Args:
            value: Slash-delimited parameter path.

        Returns:
            Parsed parameter path.

        Raises:
            ModelValidationError: If the path is malformed.
        """
        if not isinstance(value, str):
            raise ModelValidationError("invalid_parameter_path", "Parameter path must be a string.")
        parts = tuple(part for part in value.split("/") if part)
        if len(parts) < 3:
            raise ModelValidationError(
                "invalid_parameter_path",
                "Parameter path must include owner type, owner ID, and at least one field segment.",
                "parameter_path",
                {"value": value},
            )
        return cls(parts[0], parts[1], parts[2:])

    def __str__(self) -> str:
        """Return the canonical serialized path."""
        return "/".join((self.owner_type, self.owner_id, *self.segments))


@dataclass(frozen=True)
class UnitMetadata:
    """Unit metadata for a numeric model value.

    Args:
        symbol: Unit symbol, for example ``angstrom`` or ``degree``.
        quantity: Physical quantity represented by the unit.
        scale_to_si: Optional multiplier to convert to SI base units.
    """

    symbol: str
    quantity: str
    scale_to_si: float | None = None
    REQUIRED: ClassVar[tuple[str, ...]] = ("symbol", "quantity")

    def __post_init__(self) -> None:
        """Validate unit metadata."""
        if not self.symbol:
            raise ModelValidationError("invalid_unit", "Unit symbol must be non-empty.", "unit.symbol")
        if not self.quantity:
            raise ModelValidationError("invalid_unit", "Unit quantity must be non-empty.", "unit.quantity")
        if self.scale_to_si is not None:
            _finite_number(self.scale_to_si, "unit.scale_to_si")
            if self.scale_to_si <= 0:
                raise ModelValidationError("invalid_unit", "Unit SI scale must be positive.", "unit.scale_to_si")

    @classmethod
    def from_dict(cls, data: Any) -> UnitMetadata:
        """Create unit metadata from a mapping."""
        return _load_dataclass(cls, data, cls.REQUIRED)


@dataclass(frozen=True)
class Bounds:
    """Inclusive numeric bounds for a refinement parameter."""

    lower: float | None = None
    upper: float | None = None

    def __post_init__(self) -> None:
        """Validate finite ordered bounds."""
        if self.lower is not None:
            _finite_number(self.lower, "bounds.lower")
        if self.upper is not None:
            _finite_number(self.upper, "bounds.upper")
        if self.lower is not None and self.upper is not None and self.lower > self.upper:
            raise ModelValidationError("invalid_bounds", "Lower bound cannot exceed upper bound.", "bounds")

    @classmethod
    def from_dict(cls, data: Any) -> Bounds:
        """Create bounds from a mapping or two-item schema array."""
        if isinstance(data, list):
            if len(data) != 2:
                raise ModelValidationError("invalid_bounds", "Bounds array must contain exactly two items.", "bounds")
            return cls(data[0], data[1])
        return _load_dataclass(cls, data, ())

    def to_schema_list(self) -> list[float | None]:
        """Return the schema-compatible two-item representation."""
        return [self.lower, self.upper]


@dataclass(frozen=True)
class Prior:
    """Prior distribution metadata for a refinement parameter."""

    distribution: str
    parameters: dict[str, float] = field(default_factory=dict)
    REQUIRED: ClassVar[tuple[str, ...]] = ("distribution",)

    def __post_init__(self) -> None:
        """Validate prior metadata."""
        if not self.distribution:
            raise ModelValidationError("invalid_prior", "Prior distribution must be non-empty.", "prior.distribution")
        for name, value in self.parameters.items():
            _finite_number(value, f"prior.parameters.{name}")

    @classmethod
    def from_dict(cls, data: Any) -> Prior:
        """Create prior metadata from a mapping."""
        return _load_dataclass(cls, data, cls.REQUIRED)


@dataclass(frozen=True)
class DetectorBank:
    """Detector-bank metadata and bank-specific calibration references."""

    id: str
    name: str | None = None
    axis: AxisType | None = None
    calibration: dict[str, Any] = field(default_factory=dict)
    mask_uri: str | None = None
    REQUIRED: ClassVar[tuple[str, ...]] = ("id",)

    def __post_init__(self) -> None:
        """Validate detector-bank identity."""
        validate_entity_id(self.id, "detector_bank.id")

    @classmethod
    def from_dict(cls, data: Any) -> DetectorBank:
        """Create a detector bank from a mapping."""
        return _load_dataclass(cls, data, cls.REQUIRED)


@dataclass(frozen=True)
class Instrument:
    """Instrument metadata with detector banks."""

    id: str
    radiation: RadiationType
    name: str | None = None
    detector_banks: list[DetectorBank] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    REQUIRED: ClassVar[tuple[str, ...]] = ("id", "radiation")

    def __post_init__(self) -> None:
        """Validate instrument identity and bank IDs."""
        validate_entity_id(self.id, "instrument.id")
        _ensure_unique_ids(self.detector_banks, "instrument.detector_banks")

    @classmethod
    def from_dict(cls, data: Any) -> Instrument:
        """Create an instrument from a mapping."""
        return _load_dataclass(cls, data, cls.REQUIRED)


@dataclass(frozen=True)
class Histogram:
    """Refinement-ready profile metadata."""

    id: str
    dataset_id: str
    bank_id: str
    x_uri: str
    y_uri: str
    sigma_uri: str | None = None
    background_model: dict[str, Any] = field(default_factory=dict)
    phase_ids: list[str] = field(default_factory=list)
    REQUIRED: ClassVar[tuple[str, ...]] = ("id", "dataset_id", "bank_id", "x_uri", "y_uri")

    def __post_init__(self) -> None:
        """Validate histogram references."""
        validate_entity_id(self.id, "histogram.id")
        validate_entity_id(self.dataset_id, "histogram.dataset_id")
        validate_entity_id(self.bank_id, "histogram.bank_id")
        for phase_id in self.phase_ids:
            validate_entity_id(phase_id, "histogram.phase_ids")

    @classmethod
    def from_dict(cls, data: Any) -> Histogram:
        """Create a histogram from a mapping."""
        return _load_dataclass(cls, data, cls.REQUIRED)


@dataclass(frozen=True)
class Dataset:
    """Raw or reduced measurement dataset metadata."""

    id: str
    axis: AxisType
    data_uri: str
    uncertainty_model: str = "user_supplied"
    histograms: list[Histogram] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    REQUIRED: ClassVar[tuple[str, ...]] = ("id", "axis", "data_uri")

    def __post_init__(self) -> None:
        """Validate dataset identity and histogram IDs."""
        validate_entity_id(self.id, "dataset.id")
        if not self.data_uri:
            raise ModelValidationError("invalid_uri", "Dataset data URI must be non-empty.", "dataset.data_uri")
        _ensure_unique_ids(self.histograms, "dataset.histograms")
        for histogram in self.histograms:
            if histogram.dataset_id != self.id:
                raise ModelValidationError(
                    "invalid_reference",
                    "Histogram dataset_id must match the containing dataset.",
                    "dataset.histograms",
                    {"histogram_id": histogram.id, "dataset_id": histogram.dataset_id},
                )

    @classmethod
    def from_dict(cls, data: Any) -> Dataset:
        """Create a dataset from a mapping."""
        return _load_dataclass(cls, data, cls.REQUIRED)


@dataclass(frozen=True)
class Experiment:
    """Physical measurement campaign or collection condition."""

    id: str
    radiation: RadiationType
    datasets: list[Dataset]
    instrument_id: str | None = None
    sample_environment: dict[str, Any] = field(default_factory=dict)
    REQUIRED: ClassVar[tuple[str, ...]] = ("id", "radiation", "datasets")

    def __post_init__(self) -> None:
        """Validate experiment identity and dataset IDs."""
        validate_entity_id(self.id, "experiment.id")
        if self.instrument_id is not None:
            validate_entity_id(self.instrument_id, "experiment.instrument_id")
        _ensure_unique_ids(self.datasets, "experiment.datasets")

    @classmethod
    def from_dict(cls, data: Any) -> Experiment:
        """Create an experiment from a mapping."""
        return _load_dataclass(cls, data, cls.REQUIRED)


@dataclass(frozen=True)
class CrystalStructure:
    """Crystallographic structure metadata.

    Args:
        space_group: Space-group symbol or number as supplied by an importer.
        cell: Unit-cell values keyed by conventional names such as ``a`` and
            ``alpha``. Units must be documented by the containing parameter
            definitions until a full crystallographic kernel is implemented.
        atom_sites: Atom-site records retained as metadata.
    """

    space_group: str | None = None
    cell: dict[str, float] = field(default_factory=dict)
    atom_sites: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate finite cell values."""
        for name, value in self.cell.items():
            _finite_number(value, f"crystal_structure.cell.{name}")

    @classmethod
    def from_dict(cls, data: Any) -> CrystalStructure:
        """Create a crystal structure from a mapping."""
        return _load_dataclass(cls, data, ())


@dataclass(frozen=True)
class MagneticStructure:
    """Magnetic structure metadata and provenance."""

    propagation_vectors: list[list[float]] = field(default_factory=list)
    moments: list[dict[str, Any]] = field(default_factory=list)
    symmetry: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate propagation vector shapes."""
        for index, vector in enumerate(self.propagation_vectors):
            if len(vector) != 3:
                raise ModelValidationError(
                    "invalid_vector",
                    "Propagation vectors must contain exactly three components.",
                    f"magnetic_structure.propagation_vectors.{index}",
                )
            for component in vector:
                _finite_number(component, f"magnetic_structure.propagation_vectors.{index}")

    @classmethod
    def from_dict(cls, data: Any) -> MagneticStructure:
        """Create a magnetic structure from a mapping."""
        return _load_dataclass(cls, data, ())


@dataclass(frozen=True)
class Phase:
    """Material phase with structural metadata."""

    id: str
    name: str
    crystal_structure: CrystalStructure
    magnetic_structure: MagneticStructure | None = None
    microstructure_model: dict[str, Any] = field(default_factory=dict)
    texture_model: dict[str, Any] = field(default_factory=dict)
    REQUIRED: ClassVar[tuple[str, ...]] = ("id", "name", "crystal_structure")

    def __post_init__(self) -> None:
        """Validate phase identity."""
        validate_entity_id(self.id, "phase.id")
        if not self.name:
            raise ModelValidationError("invalid_name", "Phase name must be non-empty.", "phase.name")

    @classmethod
    def from_dict(cls, data: Any) -> Phase:
        """Create a phase from a mapping."""
        return _load_dataclass(cls, data, cls.REQUIRED)


@dataclass(frozen=True)
class RefinementParameter:
    """Typed variable in the global parameter graph."""

    id: str
    path: ParameterPath
    value: float
    refine: bool
    unit: UnitMetadata | None = None
    standard_uncertainty: float | None = None
    bounds: Bounds | None = None
    prior: Prior | None = None
    owner_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    REQUIRED: ClassVar[tuple[str, ...]] = ("id", "path", "value", "refine")

    def __post_init__(self) -> None:
        """Validate parameter value, bounds, and ownership."""
        validate_entity_id(self.id, "parameter.id")
        _finite_number(self.value, "parameter.value")
        if not isinstance(self.refine, bool):
            raise ModelValidationError("invalid_type", "Parameter refine flag must be a boolean.", "parameter.refine")
        if self.standard_uncertainty is not None:
            _finite_number(self.standard_uncertainty, "parameter.standard_uncertainty")
            if self.standard_uncertainty < 0:
                raise ModelValidationError(
                    "invalid_uncertainty",
                    "Standard uncertainty cannot be negative.",
                    "parameter.standard_uncertainty",
                )
        if self.bounds is not None:
            if self.bounds.lower is not None and self.value < self.bounds.lower:
                raise ModelValidationError("value_out_of_bounds", "Parameter value is below lower bound.", self.id)
            if self.bounds.upper is not None and self.value > self.bounds.upper:
                raise ModelValidationError("value_out_of_bounds", "Parameter value is above upper bound.", self.id)
        if self.owner_id is not None:
            validate_entity_id(self.owner_id, "parameter.owner_id")

    @classmethod
    def from_dict(cls, data: Any) -> RefinementParameter:
        """Create a refinement parameter from a mapping."""
        mapping = _require_mapping(data, cls.__name__)
        if "units" in mapping and "unit" not in mapping:
            mapping = dict(mapping)
            mapping["unit"] = {"symbol": mapping.pop("units"), "quantity": "unspecified"}
        if isinstance(mapping.get("bounds"), list):
            mapping = dict(mapping)
            mapping["bounds"] = Bounds.from_dict(mapping["bounds"])
        return _load_dataclass(cls, mapping, cls.REQUIRED)

    def to_schema_dict(self) -> dict[str, Any]:
        """Return the representation expected by ``schemas/project.schema.json``."""
        data = self.to_dict()
        if self.bounds is not None:
            data["bounds"] = self.bounds.to_schema_list()
        data["path"] = str(self.path)
        return data

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""
        return _serialize(self)


@dataclass(frozen=True)
class Constraint:
    """Relation among refinement parameters."""

    id: str
    kind: ConstraintKind
    expression: str
    parameter_ids: list[str] = field(default_factory=list)
    REQUIRED: ClassVar[tuple[str, ...]] = ("id", "kind", "expression")

    def __post_init__(self) -> None:
        """Validate constraint identity and referenced parameter IDs."""
        validate_entity_id(self.id, "constraint.id")
        if not self.expression:
            raise ModelValidationError("invalid_expression", "Constraint expression must be non-empty.", "constraint")
        for parameter_id in self.parameter_ids:
            validate_entity_id(parameter_id, "constraint.parameter_ids")

    @classmethod
    def from_dict(cls, data: Any) -> Constraint:
        """Create a constraint from a mapping."""
        return _load_dataclass(cls, data, cls.REQUIRED)


@dataclass(frozen=True)
class OptimizationStrategy:
    """Reproducible refinement recipe metadata."""

    id: str
    method: OptimizationMethod
    parameter_ids: list[str] = field(default_factory=list)
    stopping_criteria: dict[str, Any] = field(default_factory=dict)
    diagnostics: list[str] = field(default_factory=list)
    REQUIRED: ClassVar[tuple[str, ...]] = ("id", "method")

    def __post_init__(self) -> None:
        """Validate optimization strategy references."""
        validate_entity_id(self.id, "optimization_strategy.id")
        for parameter_id in self.parameter_ids:
            validate_entity_id(parameter_id, "optimization_strategy.parameter_ids")

    @classmethod
    def from_dict(cls, data: Any) -> OptimizationStrategy:
        """Create an optimization strategy from a mapping."""
        return _load_dataclass(cls, data, cls.REQUIRED)


@dataclass(frozen=True)
class SequentialPoint:
    """Single point in a sequential study."""

    id: str
    dataset_id: str
    variables: dict[str, float] = field(default_factory=dict)
    REQUIRED: ClassVar[tuple[str, ...]] = ("id", "dataset_id")

    def __post_init__(self) -> None:
        """Validate sequential point identity and variables."""
        validate_entity_id(self.id, "sequential_point.id")
        validate_entity_id(self.dataset_id, "sequential_point.dataset_id")
        for name, value in self.variables.items():
            _finite_number(value, f"sequential_point.variables.{name}")

    @classmethod
    def from_dict(cls, data: Any) -> SequentialPoint:
        """Create a sequential point from a mapping."""
        return _load_dataclass(cls, data, cls.REQUIRED)


@dataclass(frozen=True)
class SequentialStudy:
    """Collection of related datasets with varying external variables."""

    id: str
    points: list[SequentialPoint] = field(default_factory=list)
    shared_parameter_ids: list[str] = field(default_factory=list)
    REQUIRED: ClassVar[tuple[str, ...]] = ("id",)

    def __post_init__(self) -> None:
        """Validate sequential study references."""
        validate_entity_id(self.id, "sequential_study.id")
        _ensure_unique_ids(self.points, "sequential_study.points")
        for parameter_id in self.shared_parameter_ids:
            validate_entity_id(parameter_id, "sequential_study.shared_parameter_ids")

    @classmethod
    def from_dict(cls, data: Any) -> SequentialStudy:
        """Create a sequential study from a mapping."""
        return _load_dataclass(cls, data, cls.REQUIRED)


@dataclass(frozen=True)
class Provenance:
    """Project creation and action-log metadata."""

    created_by: str | None = None
    created_at: str | None = None
    software: dict[str, Any] = field(default_factory=dict)
    actions: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Any) -> Provenance:
        """Create provenance metadata from a mapping."""
        return _load_dataclass(cls, data, ())


@dataclass(frozen=True)
class Project:
    """Top-level project model graph."""

    id: str
    experiments: list[Experiment]
    phases: list[Phase]
    parameters: list[RefinementParameter]
    schema_version: str = "1.0.0"
    name: str | None = None
    instruments: list[Instrument] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    strategies: list[OptimizationStrategy] = field(default_factory=list)
    studies: list[SequentialStudy] = field(default_factory=list)
    provenance: Provenance | None = None
    REQUIRED: ClassVar[tuple[str, ...]] = ("schema_version", "id", "experiments", "phases", "parameters")

    def __post_init__(self) -> None:
        """Validate model graph identity, references, and schema version."""
        validate_entity_id(self.id, "project.id")
        if SCHEMA_VERSION_PATTERN.fullmatch(self.schema_version) is None:
            raise ModelValidationError(
                "invalid_schema_version",
                "Project schema_version must match the 1.0.x compatibility line.",
                "project.schema_version",
                {"value": self.schema_version},
            )
        _ensure_unique_ids(self.experiments, "project.experiments")
        _ensure_unique_ids(self.phases, "project.phases")
        _ensure_unique_ids(self.parameters, "project.parameters")
        _ensure_unique_ids(self.instruments, "project.instruments")
        _ensure_unique_ids(self.constraints, "project.constraints")
        _ensure_unique_ids(self.strategies, "project.strategies")
        _ensure_unique_ids(self.studies, "project.studies")
        self._validate_references()

    @classmethod
    def from_dict(cls, data: Any) -> Project:
        """Create a project from a mapping.

        Args:
            data: JSON-compatible project mapping.

        Returns:
            Project instance.

        Raises:
            ModelValidationError: If required fields or references are invalid.
        """
        return _load_dataclass(cls, data, cls.REQUIRED)

    @classmethod
    def from_json(cls, payload: str) -> Project:
        """Deserialize a project from deterministic JSON text."""
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ModelValidationError("invalid_json", "Project JSON could not be decoded.") from exc
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""
        return _serialize(self)

    def to_schema_dict(self) -> dict[str, Any]:
        """Return a mapping compatible with ``schemas/project.schema.json``."""
        data = self.to_dict()
        data["parameters"] = [parameter.to_schema_dict() for parameter in self.parameters]
        return data

    def to_json(self) -> str:
        """Serialize the project to stable JSON text."""
        return json.dumps(self.to_schema_dict(), sort_keys=True, separators=(",", ":"))

    def parameter_map(self) -> dict[str, RefinementParameter]:
        """Return parameters keyed by stable ID."""
        return {parameter.id: parameter for parameter in self.parameters}

    def diff(self, other: Project) -> dict[str, list[str]]:
        """Compare two project graphs by stable entity IDs.

        Args:
            other: Project to compare against this project.

        Returns:
            Mapping from entity collection name to changed entity IDs.
        """
        changes: dict[str, list[str]] = {}
        top_level = {
            "id": self.id,
            "schema_version": self.schema_version,
            "name": self.name,
        }
        other_top_level = {
            "id": other.id,
            "schema_version": other.schema_version,
            "name": other.name,
        }
        if top_level != other_top_level:
            changes["project"] = sorted({self.id, other.id})

        for name in ("instruments", "experiments", "phases", "parameters", "constraints", "strategies", "studies"):
            left = {item.id: item.to_dict() if hasattr(item, "to_dict") else _serialize(item) for item in getattr(self, name)}
            right = {item.id: item.to_dict() if hasattr(item, "to_dict") else _serialize(item) for item in getattr(other, name)}
            changed = sorted((set(left) | set(right)) - {key for key in set(left) & set(right) if left[key] == right[key]})
            if changed:
                changes[name] = changed
        if _serialize(self.provenance) != _serialize(other.provenance):
            changes["provenance"] = [self.id]
        return changes

    def _validate_references(self) -> None:
        phase_ids = {phase.id for phase in self.phases}
        instrument_ids = {instrument.id for instrument in self.instruments}
        bank_ids = {bank.id for instrument in self.instruments for bank in instrument.detector_banks}
        dataset_ids: set[str] = set()
        for experiment in self.experiments:
            if experiment.instrument_id is not None and instrument_ids and experiment.instrument_id not in instrument_ids:
                raise ModelValidationError(
                    "invalid_reference",
                    "Experiment references an unknown instrument_id.",
                    "project.experiments",
                    {"experiment_id": experiment.id, "instrument_id": experiment.instrument_id},
                )
            for dataset in experiment.datasets:
                dataset_ids.add(dataset.id)
                for histogram in dataset.histograms:
                    if bank_ids and histogram.bank_id not in bank_ids:
                        raise ModelValidationError(
                            "invalid_reference",
                            "Histogram references an unknown detector bank.",
                            "project.experiments.datasets.histograms",
                            {"histogram_id": histogram.id, "bank_id": histogram.bank_id},
                        )
                    unknown_phases = sorted(set(histogram.phase_ids) - phase_ids)
                    if unknown_phases:
                        raise ModelValidationError(
                            "invalid_reference",
                            "Histogram references unknown phase IDs.",
                            "project.experiments.datasets.histograms",
                            {"histogram_id": histogram.id, "phase_ids": unknown_phases},
                        )
        parameter_ids = {parameter.id for parameter in self.parameters}
        for constraint in self.constraints:
            unknown_parameters = sorted(set(constraint.parameter_ids) - parameter_ids)
            if unknown_parameters:
                raise ModelValidationError(
                    "invalid_reference",
                    "Constraint references unknown parameter IDs.",
                    "project.constraints",
                    {"constraint_id": constraint.id, "parameter_ids": unknown_parameters},
                )
        for strategy in self.strategies:
            unknown_parameters = sorted(set(strategy.parameter_ids) - parameter_ids)
            if unknown_parameters:
                raise ModelValidationError(
                    "invalid_reference",
                    "Optimization strategy references unknown parameter IDs.",
                    "project.strategies",
                    {"strategy_id": strategy.id, "parameter_ids": unknown_parameters},
                )
        for study in self.studies:
            unknown_parameters = sorted(set(study.shared_parameter_ids) - parameter_ids)
            if unknown_parameters:
                raise ModelValidationError(
                    "invalid_reference",
                    "Sequential study references unknown shared parameter IDs.",
                    "project.studies",
                    {"study_id": study.id, "parameter_ids": unknown_parameters},
                )
            for point in study.points:
                if point.dataset_id not in dataset_ids:
                    raise ModelValidationError(
                        "invalid_reference",
                        "Sequential point references an unknown dataset.",
                        "project.studies.points",
                        {"point_id": point.id, "dataset_id": point.dataset_id},
                    )


def _ensure_unique_ids(items: list[Any], path: str) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for item in items:
        item_id = getattr(item, "id", None)
        if item_id in seen:
            duplicates.append(item_id)
        seen.add(item_id)
    if duplicates:
        raise ModelValidationError("duplicate_id", "Entity IDs must be unique within a collection.", path, {"ids": duplicates})
