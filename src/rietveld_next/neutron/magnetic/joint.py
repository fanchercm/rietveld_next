"""Joint nuclear-magnetic refinement helpers for startup workflows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import math
from typing import Any

from rietveld_next.neutron.magnetic.moment import MagneticMoment
from rietveld_next.neutron.magnetic.propagation import PropagationVector
from rietveld_next.neutron.magnetic.symmetry import magnetic_moment_parameter_id


REFLECTION_KINDS = frozenset(
    {"nuclear", "magnetic_satellite", "mixed_nuclear_magnetic", "unindexed"}
)


@dataclass(frozen=True)
class NuclearMagneticPhaseCoupling:
    """Toggle and scale nuclear and magnetic contributions for one phase.

    Args:
        phase_id: Stable phase identifier.
        nuclear_enabled: Whether nuclear intensity contributes to the sum.
        magnetic_enabled: Whether magnetic intensity contributes to the sum.
        nuclear_scale: Non-negative relative scale applied to nuclear intensity.
        magnetic_scale: Non-negative relative scale applied to magnetic intensity.
        magnetic_site_ids: Magnetic site identifiers coupled to the phase.
        units: Intensity units. The startup API supports only
            ``relative_intensity``.

    Raises:
        ValueError: If identifiers, scales, units, or intensity vectors are
            invalid.

    Example:
        >>> coupling = NuclearMagneticPhaseCoupling("phase1", magnetic_site_ids=("mn1",))
        >>> coupling.combine([10.0], [2.0])
        (12.0,)
    """

    phase_id: str
    nuclear_enabled: bool = True
    magnetic_enabled: bool = True
    nuclear_scale: float = 1.0
    magnetic_scale: float = 1.0
    magnetic_site_ids: tuple[str, ...] = ()
    units: str = "relative_intensity"

    def __post_init__(self) -> None:
        """Validate phase identity, toggles, scale bounds, and site IDs."""

        _non_empty_string(self.phase_id, "phase_id")
        if not isinstance(self.nuclear_enabled, bool):
            raise ValueError("nuclear_enabled must be a boolean.")
        if not isinstance(self.magnetic_enabled, bool):
            raise ValueError("magnetic_enabled must be a boolean.")
        if self.units != "relative_intensity":
            raise ValueError("units must be 'relative_intensity'.")
        site_ids = _string_tuple(self.magnetic_site_ids, "magnetic_site_ids", allow_empty=True)
        object.__setattr__(
            self,
            "nuclear_scale",
            _non_negative_finite_float(self.nuclear_scale, "nuclear_scale"),
        )
        object.__setattr__(
            self,
            "magnetic_scale",
            _non_negative_finite_float(self.magnetic_scale, "magnetic_scale"),
        )
        object.__setattr__(self, "magnetic_site_ids", site_ids)

    def combine(
        self,
        nuclear_intensity: Sequence[float],
        magnetic_intensity: Sequence[float],
    ) -> tuple[float, ...]:
        """Return the toggled nuclear-plus-magnetic intensity vector.

        Args:
            nuclear_intensity: Non-negative nuclear relative-intensity values.
            magnetic_intensity: Non-negative magnetic relative-intensity values.

        Returns:
            Element-wise sum after applying contribution toggles and scales.

        Raises:
            ValueError: If vectors differ in length or contain invalid values.
        """

        nuclear = _non_negative_vector(nuclear_intensity, "nuclear_intensity")
        magnetic = _non_negative_vector(magnetic_intensity, "magnetic_intensity")
        if len(nuclear) != len(magnetic):
            raise ValueError("nuclear_intensity and magnetic_intensity must have the same length.")
        nuclear_scale = self.nuclear_scale if self.nuclear_enabled else 0.0
        magnetic_scale = self.magnetic_scale if self.magnetic_enabled else 0.0
        return tuple(
            nuclear_scale * nuclear_value + magnetic_scale * magnetic_value
            for nuclear_value, magnetic_value in zip(nuclear, magnetic, strict=True)
        )

    def separate_contributions(
        self,
        nuclear_intensity: Sequence[float],
        magnetic_intensity: Sequence[float],
    ) -> dict[str, tuple[float, ...]]:
        """Return separately scaled nuclear, magnetic, and total vectors."""

        nuclear = _non_negative_vector(nuclear_intensity, "nuclear_intensity")
        magnetic = _non_negative_vector(magnetic_intensity, "magnetic_intensity")
        if len(nuclear) != len(magnetic):
            raise ValueError("nuclear_intensity and magnetic_intensity must have the same length.")
        scaled_nuclear = tuple(
            (self.nuclear_scale if self.nuclear_enabled else 0.0) * value for value in nuclear
        )
        scaled_magnetic = tuple(
            (self.magnetic_scale if self.magnetic_enabled else 0.0) * value for value in magnetic
        )
        total = tuple(
            nuclear_value + magnetic_value
            for nuclear_value, magnetic_value in zip(scaled_nuclear, scaled_magnetic, strict=True)
        )
        return {
            "nuclear": scaled_nuclear,
            "magnetic": scaled_magnetic,
            "total": total,
        }

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible coupling record."""

        return {
            "phase_id": self.phase_id,
            "nuclear_enabled": self.nuclear_enabled,
            "magnetic_enabled": self.magnetic_enabled,
            "nuclear_scale": self.nuclear_scale,
            "magnetic_scale": self.magnetic_scale,
            "magnetic_site_ids": list(self.magnetic_site_ids),
            "units": self.units,
        }


@dataclass(frozen=True)
class ReflectionCandidate:
    """Reflection coordinate to classify for magnetic refinement.

    Args:
        indices_rlu: Three Miller-index coordinates in reciprocal lattice units.
        label: Optional deterministic label for reporting.
    """

    indices_rlu: tuple[float, float, float]
    label: str | None = None

    def __post_init__(self) -> None:
        """Validate reciprocal-lattice-unit coordinates and label."""

        object.__setattr__(
            self,
            "indices_rlu",
            _three_finite_components(self.indices_rlu, "indices_rlu"),
        )
        if self.label is not None:
            _non_empty_string(self.label, "label")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible reflection candidate."""

        return {
            "indices_rlu": list(self.indices_rlu),
            "label": self.label,
            "units": "reciprocal_lattice_units",
        }


@dataclass(frozen=True)
class MagneticReflectionFlag:
    """Classification result for a reflection candidate.

    Args:
        indices_rlu: Reflection coordinate in reciprocal lattice units.
        kind: One of ``nuclear``, ``magnetic_satellite``,
            ``mixed_nuclear_magnetic``, or ``unindexed``.
        base_hkl: Nearest integer parent Miller indices.
        propagation_vector_id: Matching propagation-vector ID, if any.
        satellite_sign: ``+1`` or ``-1`` for a magnetic satellite, otherwise
            ``0``.
        reason: Short deterministic explanation for audit logs.
        label: Optional source candidate label.
    """

    indices_rlu: tuple[float, float, float]
    kind: str
    base_hkl: tuple[int, int, int]
    propagation_vector_id: str | None
    satellite_sign: int
    reason: str
    label: str | None = None

    def __post_init__(self) -> None:
        """Validate reflection classification fields."""

        object.__setattr__(
            self,
            "indices_rlu",
            _three_finite_components(self.indices_rlu, "indices_rlu"),
        )
        if self.kind not in REFLECTION_KINDS:
            allowed = ", ".join(sorted(REFLECTION_KINDS))
            raise ValueError(f"kind must be one of: {allowed}.")
        if (
            isinstance(self.base_hkl, str)
            or not isinstance(self.base_hkl, Sequence)
            or len(self.base_hkl) != 3
        ):
            raise ValueError("base_hkl must be a three-item integer sequence.")
        base_hkl = tuple(_integer(value, f"base_hkl[{index}]") for index, value in enumerate(self.base_hkl))
        if self.propagation_vector_id is not None:
            _non_empty_string(self.propagation_vector_id, "propagation_vector_id")
        if self.satellite_sign not in (-1, 0, 1):
            raise ValueError("satellite_sign must be -1, 0, or 1.")
        _non_empty_string(self.reason, "reason")
        if self.label is not None:
            _non_empty_string(self.label, "label")
        object.__setattr__(self, "base_hkl", base_hkl)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible reflection flag."""

        return {
            "indices_rlu": list(self.indices_rlu),
            "kind": self.kind,
            "base_hkl": list(self.base_hkl),
            "propagation_vector_id": self.propagation_vector_id,
            "satellite_sign": self.satellite_sign,
            "reason": self.reason,
            "label": self.label,
            "units": "reciprocal_lattice_units",
        }


@dataclass(frozen=True)
class MagneticParameterGroupRecipe:
    """Safe staged magnetic-parameter group recipe.

    Args:
        recipe_id: Stable recipe identifier.
        stage: Positive stage number.
        label: Human-readable group label.
        parameter_ids: Parameter IDs included in the group.
        default_action: Startup action for this group.
        rationale: Short scientific rationale or limitation.
        bounds: Optional parameter bounds keyed by parameter ID.
    """

    recipe_id: str
    stage: int
    label: str
    parameter_ids: tuple[str, ...]
    default_action: str
    rationale: str
    bounds: Mapping[str, tuple[float, float]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate recipe identity, staged order, and finite bounds."""

        _non_empty_string(self.recipe_id, "recipe_id")
        if not isinstance(self.stage, int) or isinstance(self.stage, bool) or self.stage < 1:
            raise ValueError("stage must be a positive integer.")
        _non_empty_string(self.label, "label")
        parameter_ids = _string_tuple(self.parameter_ids, "parameter_ids", allow_empty=False)
        _non_empty_string(self.default_action, "default_action")
        _non_empty_string(self.rationale, "rationale")
        bounds = _bounds_mapping(self.bounds, set(parameter_ids))
        object.__setattr__(self, "parameter_ids", parameter_ids)
        object.__setattr__(self, "bounds", bounds)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible recipe record."""

        return {
            "recipe_id": self.recipe_id,
            "stage": self.stage,
            "label": self.label,
            "parameter_ids": list(self.parameter_ids),
            "default_action": self.default_action,
            "rationale": self.rationale,
            "bounds": {
                parameter_id: list(values)
                for parameter_id, values in sorted(self.bounds.items())
            },
        }


@dataclass(frozen=True)
class MagneticTutorialDataset:
    """Small deterministic magnetic refinement tutorial fixture.

    The fixture is synthetic and records relative intensities only. It is for
    workflow wiring, reports, and regression tests, not reference validation of
    magnetic structure-factor physics.
    """

    dataset_id: str
    coupling: NuclearMagneticPhaseCoupling
    propagation_vectors: tuple[PropagationVector, ...]
    moments: tuple[MagneticMoment, ...]
    reflection_flags: tuple[MagneticReflectionFlag, ...]
    nuclear_intensity: tuple[float, ...]
    magnetic_intensity: tuple[float, ...]
    observed_counts: tuple[float, ...]
    notes: tuple[str, ...] = (
        "Synthetic startup fixture with relative intensities.",
        "Not cross-software validation of magnetic structure factors.",
    )

    def __post_init__(self) -> None:
        """Validate tutorial dataset shape and finite non-negative values."""

        _non_empty_string(self.dataset_id, "dataset_id")
        if not isinstance(self.coupling, NuclearMagneticPhaseCoupling):
            raise ValueError("coupling must be a NuclearMagneticPhaseCoupling.")
        vectors = _typed_tuple(self.propagation_vectors, PropagationVector, "propagation_vectors")
        moments = _typed_tuple(self.moments, MagneticMoment, "moments")
        flags = _typed_tuple(self.reflection_flags, MagneticReflectionFlag, "reflection_flags")
        nuclear = _non_negative_vector(self.nuclear_intensity, "nuclear_intensity")
        magnetic = _non_negative_vector(self.magnetic_intensity, "magnetic_intensity")
        observed = _non_negative_vector(self.observed_counts, "observed_counts")
        if not (len(flags) == len(nuclear) == len(magnetic) == len(observed)):
            raise ValueError("reflection flags and intensity vectors must have the same length.")
        notes = _string_tuple(self.notes, "notes", allow_empty=False)
        object.__setattr__(self, "propagation_vectors", vectors)
        object.__setattr__(self, "moments", moments)
        object.__setattr__(self, "reflection_flags", flags)
        object.__setattr__(self, "nuclear_intensity", nuclear)
        object.__setattr__(self, "magnetic_intensity", magnetic)
        object.__setattr__(self, "observed_counts", observed)
        object.__setattr__(self, "notes", notes)

    @property
    def calculated_intensity(self) -> tuple[float, ...]:
        """Return coupled calculated relative intensities."""

        return self.coupling.combine(self.nuclear_intensity, self.magnetic_intensity)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible tutorial fixture."""

        return {
            "dataset_id": self.dataset_id,
            "coupling": self.coupling.to_dict(),
            "propagation_vectors": [vector.to_dict() for vector in self.propagation_vectors],
            "moments": [moment.to_dict() for moment in self.moments],
            "reflection_flags": [flag.to_dict() for flag in self.reflection_flags],
            "nuclear_intensity": list(self.nuclear_intensity),
            "magnetic_intensity": list(self.magnetic_intensity),
            "calculated_intensity": list(self.calculated_intensity),
            "observed_counts": list(self.observed_counts),
            "notes": list(self.notes),
        }


def flag_magnetic_reflections(
    reflections: Sequence[ReflectionCandidate | Sequence[float]],
    propagation_vectors: Sequence[PropagationVector],
    *,
    tolerance_rlu: float = 1.0e-8,
) -> tuple[MagneticReflectionFlag, ...]:
    """Classify reflections as nuclear, magnetic satellites, mixed, or unindexed.

    Args:
        reflections: Reflection candidates as ``ReflectionCandidate`` records or
            three-component reciprocal-lattice-unit coordinates.
        propagation_vectors: Propagation vectors used to identify satellites.
        tolerance_rlu: Absolute tolerance in reciprocal lattice units.

    Returns:
        Reflection flags in input order.

    Raises:
        ValueError: If inputs are malformed or tolerance is invalid.
    """

    tolerance = _positive_finite_float(tolerance_rlu, "tolerance_rlu")
    vectors = tuple(sorted(_typed_tuple(propagation_vectors, PropagationVector, "propagation_vectors"), key=lambda item: item.vector_id))
    candidates = tuple(_reflection_candidate(item) for item in reflections)
    flags: list[MagneticReflectionFlag] = []
    for candidate in candidates:
        base_hkl = tuple(int(round(value)) for value in candidate.indices_rlu)
        offset = tuple(
            value - base_value
            for value, base_value in zip(candidate.indices_rlu, base_hkl, strict=True)
        )
        is_nuclear = all(abs(value) <= tolerance for value in offset)
        match = _match_propagation_vector(offset, vectors, tolerance)
        if is_nuclear and match is not None:
            vector_id, sign = match
            kind = "mixed_nuclear_magnetic"
            reason = "integer hkl coincides with zero propagation-vector satellite"
            satellite_sign = sign
            propagation_vector_id: str | None = vector_id
        elif match is not None:
            vector_id, sign = match
            kind = "magnetic_satellite"
            reason = f"offset matches {sign:+d} propagation vector {vector_id}"
            satellite_sign = sign
            propagation_vector_id = vector_id
        elif is_nuclear:
            kind = "nuclear"
            reason = "indices are integer hkl within tolerance"
            satellite_sign = 0
            propagation_vector_id = None
        else:
            kind = "unindexed"
            reason = "offset does not match integer hkl or supplied propagation vectors"
            satellite_sign = 0
            propagation_vector_id = None
        flags.append(
            MagneticReflectionFlag(
                indices_rlu=candidate.indices_rlu,
                kind=kind,
                base_hkl=base_hkl,
                propagation_vector_id=propagation_vector_id,
                satellite_sign=satellite_sign,
                reason=reason,
                label=candidate.label,
            )
        )
    return tuple(flags)


def build_magnetic_parameter_group_recipes(
    phase_id: str,
    site_ids: Sequence[str],
    *,
    max_moment_bohr_magneton: float = 10.0,
) -> tuple[MagneticParameterGroupRecipe, ...]:
    """Build deterministic staged recipes for magnetic refinement parameters.

    Args:
        phase_id: Owning phase identifier.
        site_ids: Magnetic site identifiers.
        max_moment_bohr_magneton: Inclusive magnitude-component guard bound in
            Bohr magnetons used for startup recipes.

    Returns:
        Three staged recipe records: magnetic scale, longitudinal moment
        components, and transverse components.

    Raises:
        ValueError: If identifiers or bounds are invalid.
    """

    phase = _non_empty_string(phase_id, "phase_id")
    sites = _string_tuple(site_ids, "site_ids", allow_empty=False)
    max_moment = _positive_finite_float(max_moment_bohr_magneton, "max_moment_bohr_magneton")
    scale_parameter_id = "p_" + "_".join(("phase", phase, "magnetic_scale"))
    max_scale = 1.0e6
    longitudinal = tuple(magnetic_moment_parameter_id(phase, site_id, "mz") for site_id in sites)
    transverse = tuple(
        magnetic_moment_parameter_id(phase, site_id, component)
        for site_id in sites
        for component in ("mx", "my")
    )
    moment_bounds = {
        parameter_id: (-max_moment, max_moment)
        for parameter_id in (*longitudinal, *transverse)
    }
    return (
        MagneticParameterGroupRecipe(
            recipe_id=f"{phase}:magnetic_scale",
            stage=1,
            label="Magnetic scale after nuclear baseline",
            parameter_ids=(scale_parameter_id,),
            default_action="refine_with_nuclear_fixed",
            rationale="Separates magnetic scale from the nuclear baseline before moment components move.",
            bounds={scale_parameter_id: (0.0, max_scale)},
        ),
        MagneticParameterGroupRecipe(
            recipe_id=f"{phase}:longitudinal_moments",
            stage=2,
            label="Longitudinal moment components",
            parameter_ids=longitudinal,
            default_action="refine_collinear_axis",
            rationale="Starts from the ordered-axis component to reduce underconstrained transverse motion.",
            bounds={parameter_id: moment_bounds[parameter_id] for parameter_id in longitudinal},
        ),
        MagneticParameterGroupRecipe(
            recipe_id=f"{phase}:transverse_moments",
            stage=3,
            label="Transverse moment components",
            parameter_ids=transverse,
            default_action="release_after_stable_scale_and_axis",
            rationale="Delays transverse components until scale and primary axis are stable.",
            bounds={parameter_id: moment_bounds[parameter_id] for parameter_id in transverse},
        ),
    )


def create_magnetic_refinement_tutorial_dataset() -> MagneticTutorialDataset:
    """Create a deterministic synthetic tutorial dataset for magnetic workflows.

    Returns:
        Synthetic dataset with nuclear and magnetic contributions reported
        separately.
    """

    vector = PropagationVector("k1", (0.5, 0.0, 0.0))
    coupling = NuclearMagneticPhaseCoupling(
        "phase_mno",
        magnetic_site_ids=("mn1", "mn2"),
    )
    candidates = (
        ReflectionCandidate((1.0, 0.0, 0.0), label="100 nuclear"),
        ReflectionCandidate((0.5, 0.0, 0.0), label="000+k magnetic"),
        ReflectionCandidate((1.5, 0.0, 0.0), label="200-k magnetic"),
        ReflectionCandidate((2.0, 0.0, 0.0), label="200 nuclear"),
    )
    return MagneticTutorialDataset(
        dataset_id="m25_synthetic_mno_collinear",
        coupling=coupling,
        propagation_vectors=(vector,),
        moments=(
            MagneticMoment("mn1", (0.0, 0.0, 3.2)),
            MagneticMoment("mn2", (0.0, 0.0, -3.2)),
        ),
        reflection_flags=flag_magnetic_reflections(candidates, (vector,)),
        nuclear_intensity=(100.0, 0.0, 0.0, 36.0),
        magnetic_intensity=(0.0, 12.0, 9.0, 0.0),
        observed_counts=(101.0, 11.8, 9.3, 35.5),
    )


def generate_magnetic_report_section(
    dataset: MagneticTutorialDataset,
    recipes: Sequence[MagneticParameterGroupRecipe] | None = None,
) -> str:
    """Generate a deterministic Markdown section for magnetic reports.

    Args:
        dataset: Tutorial or workflow dataset to summarize.
        recipes: Optional staged parameter recipes. When omitted, recipes are
            built from the dataset phase and magnetic site IDs.

    Returns:
        Markdown report section with separated nuclear/magnetic contributions.

    Raises:
        ValueError: If the dataset or recipes are invalid.
    """

    if not isinstance(dataset, MagneticTutorialDataset):
        raise ValueError("dataset must be a MagneticTutorialDataset.")
    recipe_records = (
        build_magnetic_parameter_group_recipes(
            dataset.coupling.phase_id,
            dataset.coupling.magnetic_site_ids,
        )
        if recipes is None
        else _typed_tuple(recipes, MagneticParameterGroupRecipe, "recipes")
    )
    contribution = dataset.coupling.separate_contributions(
        dataset.nuclear_intensity,
        dataset.magnetic_intensity,
    )
    counts = _reflection_kind_counts(dataset.reflection_flags)
    lines = [
        "## Magnetic refinement",
        "",
        f"- Dataset: `{dataset.dataset_id}`",
        f"- Phase: `{dataset.coupling.phase_id}`",
        f"- Nuclear enabled: `{dataset.coupling.nuclear_enabled}`",
        f"- Magnetic enabled: `{dataset.coupling.magnetic_enabled}`",
        f"- Nuclear relative intensity sum: `{sum(contribution['nuclear']):.6g}`",
        f"- Magnetic relative intensity sum: `{sum(contribution['magnetic']):.6g}`",
        f"- Total calculated relative intensity sum: `{sum(contribution['total']):.6g}`",
        "",
        "### Reflection flags",
    ]
    for kind in sorted(REFLECTION_KINDS):
        lines.append(f"- {kind}: `{counts.get(kind, 0)}`")
    lines.extend(["", "### Parameter recipes"])
    for recipe in sorted(recipe_records, key=lambda item: item.stage):
        lines.append(
            f"- Stage {recipe.stage}: `{recipe.recipe_id}` "
            f"({recipe.default_action}, {len(recipe.parameter_ids)} parameters)"
        )
    lines.extend(["", "### Limitations"])
    lines.extend(f"- {note}" for note in dataset.notes)
    return "\n".join(lines) + "\n"


def _match_propagation_vector(
    offset: tuple[float, float, float],
    vectors: Sequence[PropagationVector],
    tolerance: float,
) -> tuple[str, int] | None:
    for vector in vectors:
        for sign in (1, -1):
            if all(
                abs(offset_value - sign * vector_value) <= tolerance
                for offset_value, vector_value in zip(offset, vector.components_rlu, strict=True)
            ):
                return (vector.vector_id, sign)
    return None


def _reflection_kind_counts(flags: Sequence[MagneticReflectionFlag]) -> dict[str, int]:
    counts = {kind: 0 for kind in REFLECTION_KINDS}
    for flag in flags:
        counts[flag.kind] += 1
    return counts


def _reflection_candidate(item: ReflectionCandidate | Sequence[float]) -> ReflectionCandidate:
    if isinstance(item, ReflectionCandidate):
        return item
    return ReflectionCandidate(_three_finite_components(item, "reflection"))


def _bounds_mapping(
    bounds: Mapping[str, tuple[float, float]],
    parameter_ids: set[str],
) -> dict[str, tuple[float, float]]:
    if not isinstance(bounds, Mapping):
        raise ValueError("bounds must be a mapping.")
    normalized: dict[str, tuple[float, float]] = {}
    for key, values in bounds.items():
        parameter_id = _non_empty_string(key, "bounds key")
        if parameter_id not in parameter_ids:
            raise ValueError(f"bounds key {parameter_id!r} is not in parameter_ids.")
        if isinstance(values, str) or not isinstance(values, Sequence) or len(values) != 2:
            raise ValueError(f"bounds for {parameter_id!r} must be a two-item sequence.")
        lower = _finite_float(values[0], f"bounds[{parameter_id!r}][0]")
        upper = _finite_float(values[1], f"bounds[{parameter_id!r}][1]")
        if upper < lower:
            raise ValueError(f"bounds for {parameter_id!r} must be ordered lower <= upper.")
        normalized[parameter_id] = (lower, upper)
    return dict(sorted(normalized.items()))


def _typed_tuple(values: Sequence[Any], item_type: type[Any], name: str) -> tuple[Any, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence.")
    normalized = tuple(values)
    if not normalized:
        raise ValueError(f"{name} must not be empty.")
    for index, value in enumerate(normalized):
        if not isinstance(value, item_type):
            raise ValueError(f"{name}[{index}] must be a {item_type.__name__}.")
    return normalized


def _string_tuple(
    values: Sequence[str],
    name: str,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of strings.")
    result = tuple(_non_empty_string(value, f"{name}[{index}]") for index, value in enumerate(values))
    if not allow_empty and not result:
        raise ValueError(f"{name} must not be empty.")
    return result


def _non_negative_vector(values: Sequence[float], name: str) -> tuple[float, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite non-negative numbers.")
    result = tuple(_non_negative_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values))
    if not result:
        raise ValueError(f"{name} must not be empty.")
    return result


def _three_finite_components(values: Sequence[float], name: str) -> tuple[float, float, float]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a three-item sequence.")
    if len(values) != 3:
        raise ValueError(f"{name} must contain exactly three components.")
    components = tuple(_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values))
    return (components[0], components[1], components[2])


def _integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer.")
    return value


def _non_empty_string(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number.")
    return float(value)


def _non_negative_finite_float(value: float, name: str) -> float:
    number = _finite_float(value, name)
    if number < 0.0:
        raise ValueError(f"{name} must be non-negative.")
    return number


def _positive_finite_float(value: float, name: str) -> float:
    number = _finite_float(value, name)
    if number <= 0.0:
        raise ValueError(f"{name} must be positive.")
    return number
