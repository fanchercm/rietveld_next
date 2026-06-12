"""Small diffraction model helpers for synthetic and metadata workflows.

The helpers in this module are deterministic, dependency-free reference
implementations. They provide startup formulas and structured validation for
orientation, microstructure, background, synthetic pattern, phase fraction,
occupancy, and ADP checks. They are not substitutes for facility-validated
production refinement models.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math


_GAUSSIAN_LOG2_FACTOR = 4.0 * math.log(2.0)
_GAUSSIAN_NORMALIZATION = math.sqrt(_GAUSSIAN_LOG2_FACTOR / math.pi)
_PREFERRED_ORIENTATION_RATIO_BOUNDS = (0.1, 10.0)
_DEFAULT_TOLERANCE = 1.0e-6
_DEFAULT_ADP_U_MAX_ANGSTROM2 = 1.0
_SYNTHETIC_GENERATOR_VERSION = "synthetic-pattern-v0"


@dataclass(frozen=True)
class ModelParameterBounds:
    """Inclusive numeric bounds for a model parameter.

    Args:
        name: Stable parameter name.
        lower: Inclusive lower bound.
        upper: Inclusive upper bound.
        units: Unit label, or ``"dimensionless"`` when unitless.
        description: Short description of the bounded parameter.
    """

    name: str
    lower: float
    upper: float
    units: str
    description: str

    def __post_init__(self) -> None:
        """Validate bound metadata."""
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("ModelParameterBounds.name must be a non-empty string.")
        if not isinstance(self.units, str) or not self.units:
            raise ValueError("ModelParameterBounds.units must be a non-empty string.")
        if not isinstance(self.description, str) or not self.description:
            raise ValueError("ModelParameterBounds.description must be a non-empty string.")
        lower = _finite_float(self.lower, "ModelParameterBounds.lower")
        upper = _finite_float(self.upper, "ModelParameterBounds.upper")
        if lower > upper:
            raise ValueError("ModelParameterBounds.lower must be less than or equal to upper.")
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)


@dataclass(frozen=True)
class StructuredWarning:
    """Structured scientific validation warning.

    Args:
        code: Stable machine-readable warning code.
        message: Human-readable warning message.
        path: Deterministic path to the checked field.
        severity: ``"warning"`` or ``"error"``.
        value: Optional offending numeric value.
        bounds: Optional expected numeric bounds.
    """

    code: str
    message: str
    path: str
    severity: str = "warning"
    value: float | None = None
    bounds: tuple[float, float] | None = None

    def __post_init__(self) -> None:
        """Validate warning metadata."""
        if not isinstance(self.code, str) or not self.code:
            raise ValueError("StructuredWarning.code must be a non-empty string.")
        if not isinstance(self.message, str) or not self.message:
            raise ValueError("StructuredWarning.message must be a non-empty string.")
        if not isinstance(self.path, str) or not self.path:
            raise ValueError("StructuredWarning.path must be a non-empty string.")
        if self.severity not in {"warning", "error"}:
            raise ValueError("StructuredWarning.severity must be 'warning' or 'error'.")
        if self.value is not None:
            object.__setattr__(self, "value", _finite_float(self.value, "StructuredWarning.value"))
        if self.bounds is not None:
            lower, upper = _finite_pair(self.bounds, "StructuredWarning.bounds")
            if lower > upper:
                raise ValueError("StructuredWarning.bounds lower value must not exceed upper value.")
            object.__setattr__(self, "bounds", (lower, upper))


@dataclass(frozen=True)
class SyntheticReflection:
    """Synthetic powder reflection input.

    Args:
        phase_id: Stable phase identifier.
        hkl: Three integer Miller indices.
        two_theta_degrees: Reflection position in degrees two-theta.
        intensity: Integrated synthetic peak area before phase scaling.
        fwhm_degrees: Full width at half maximum in degrees two-theta.
    """

    phase_id: str
    hkl: tuple[int, int, int]
    two_theta_degrees: float
    intensity: float
    fwhm_degrees: float

    def __post_init__(self) -> None:
        """Validate reflection input fields."""
        if not isinstance(self.phase_id, str) or not self.phase_id:
            raise ValueError("SyntheticReflection.phase_id must be a non-empty string.")
        object.__setattr__(self, "hkl", _validate_hkl(self.hkl, "SyntheticReflection.hkl"))
        position = _finite_float(self.two_theta_degrees, "SyntheticReflection.two_theta_degrees")
        if not 0.0 < position < 180.0:
            raise ValueError(
                "SyntheticReflection.two_theta_degrees must be between 0 and 180 degrees, "
                f"got {position!r}."
            )
        intensity = _finite_float(self.intensity, "SyntheticReflection.intensity")
        if intensity < 0.0:
            raise ValueError(f"SyntheticReflection.intensity must be non-negative, got {intensity!r}.")
        fwhm = _finite_float(self.fwhm_degrees, "SyntheticReflection.fwhm_degrees")
        if fwhm <= 0.0:
            raise ValueError(f"SyntheticReflection.fwhm_degrees must be positive, got {fwhm!r}.")
        object.__setattr__(self, "two_theta_degrees", position)
        object.__setattr__(self, "intensity", intensity)
        object.__setattr__(self, "fwhm_degrees", fwhm)


@dataclass(frozen=True)
class ReflectionTick:
    """Display tick for a synthetic reflection.

    Args:
        phase_id: Phase identifier.
        hkl: Three Miller indices.
        two_theta_degrees: Tick position in degrees two-theta.
        label: Stable display label.
        intensity: Synthetic intensity proxy for sorting or styling.
    """

    phase_id: str
    hkl: tuple[int, int, int]
    two_theta_degrees: float
    label: str
    intensity: float


@dataclass(frozen=True)
class SyntheticPattern:
    """Generated synthetic one-dimensional powder pattern.

    Args:
        axis_two_theta_degrees: Sorted axis values in degrees two-theta.
        intensity: Calculated intensity values on the axis.
        phase_ticks: Reflection ticks included in the pattern.
        metadata: Deterministic metadata describing assumptions and units.
    """

    axis_two_theta_degrees: tuple[float, ...]
    intensity: tuple[float, ...]
    phase_ticks: tuple[ReflectionTick, ...]
    metadata: Mapping[str, str]


@dataclass(frozen=True)
class StandardReferenceDataset:
    """Registry entry for a reference or startup synthetic dataset.

    Args:
        dataset_id: Stable registry identifier.
        title: Human-readable title.
        category: Dataset category label.
        axis_unit: Primary axis unit.
        source: Provenance label.
        validation_status: Validation status, such as ``"synthetic-only"``.
        notes: Scope and limitation notes.
    """

    dataset_id: str
    title: str
    category: str
    axis_unit: str
    source: str
    validation_status: str
    notes: str

    def __post_init__(self) -> None:
        """Validate registry metadata."""
        for field_name in (
            "dataset_id",
            "title",
            "category",
            "axis_unit",
            "source",
            "validation_status",
            "notes",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"StandardReferenceDataset.{field_name} must be a non-empty string.")


@dataclass(frozen=True)
class PhaseScaleComponent:
    """Phase scale component used for simple fraction normalization.

    The default weight model is the startup proxy:

    ```text
    weight_proxy = scale * formula_units_per_cell * molecular_mass_g_mol
                   * cell_volume_angstrom3
    ```

    Args:
        phase_id: Stable phase identifier.
        scale: Non-negative refined or synthetic scale proxy.
        formula_units_per_cell: Positive ``Z`` proxy.
        molecular_mass_g_mol: Positive formula mass proxy.
        cell_volume_angstrom3: Positive cell volume proxy.
    """

    phase_id: str
    scale: float
    formula_units_per_cell: float = 1.0
    molecular_mass_g_mol: float = 1.0
    cell_volume_angstrom3: float = 1.0

    def __post_init__(self) -> None:
        """Validate phase scale inputs."""
        if not isinstance(self.phase_id, str) or not self.phase_id:
            raise ValueError("PhaseScaleComponent.phase_id must be a non-empty string.")
        scale = _finite_float(self.scale, "PhaseScaleComponent.scale")
        if scale < 0.0:
            raise ValueError(f"PhaseScaleComponent.scale must be non-negative, got {scale!r}.")
        object.__setattr__(self, "scale", scale)
        for field_name in ("formula_units_per_cell", "molecular_mass_g_mol", "cell_volume_angstrom3"):
            value = _finite_float(getattr(self, field_name), f"PhaseScaleComponent.{field_name}")
            if value <= 0.0:
                raise ValueError(f"PhaseScaleComponent.{field_name} must be positive, got {value!r}.")
            object.__setattr__(self, field_name, value)


@dataclass(frozen=True)
class PhaseFractionResult:
    """Normalized phase fraction result.

    Args:
        fractions: Phase fractions normalized to sum to one.
        weights: Unnormalized phase weight proxies.
        assumptions: Formula and limitation notes.
    """

    fractions: Mapping[str, float]
    weights: Mapping[str, float]
    assumptions: tuple[str, ...]


@dataclass(frozen=True)
class OccupancySite:
    """Atom occupancy record for constraint validation.

    Args:
        site_id: Stable atom-site identifier.
        occupancy: Finite occupancy value. Range checks are reported by
            :func:`validate_occupancy_constraints`.
    """

    site_id: str
    occupancy: float

    def __post_init__(self) -> None:
        """Validate site identifier and numeric occupancy."""
        if not isinstance(self.site_id, str) or not self.site_id:
            raise ValueError("OccupancySite.site_id must be a non-empty string.")
        object.__setattr__(self, "occupancy", _finite_float(self.occupancy, "OccupancySite.occupancy"))


@dataclass(frozen=True)
class OccupancyConstraint:
    """Linear atom occupancy constraint.

    Args:
        constraint_id: Stable constraint identifier.
        site_ids: Site identifiers included in the constraint.
        target_total: Expected occupancy sum.
        tolerance: Absolute tolerance on the occupancy sum.
    """

    constraint_id: str
    site_ids: tuple[str, ...]
    target_total: float = 1.0
    tolerance: float = _DEFAULT_TOLERANCE

    def __post_init__(self) -> None:
        """Validate constraint fields."""
        if not isinstance(self.constraint_id, str) or not self.constraint_id:
            raise ValueError("OccupancyConstraint.constraint_id must be a non-empty string.")
        if isinstance(self.site_ids, str) or not isinstance(self.site_ids, Sequence):
            raise ValueError("OccupancyConstraint.site_ids must be a sequence of site identifiers.")
        site_ids = tuple(self.site_ids)
        if not site_ids or any(not isinstance(site_id, str) or not site_id for site_id in site_ids):
            raise ValueError("OccupancyConstraint.site_ids must contain non-empty strings.")
        if len(set(site_ids)) != len(site_ids):
            raise ValueError("OccupancyConstraint.site_ids must not contain duplicates.")
        target = _finite_float(self.target_total, "OccupancyConstraint.target_total")
        tolerance = _finite_float(self.tolerance, "OccupancyConstraint.tolerance")
        if tolerance < 0.0:
            raise ValueError(f"OccupancyConstraint.tolerance must be non-negative, got {tolerance!r}.")
        object.__setattr__(self, "site_ids", site_ids)
        object.__setattr__(self, "target_total", target)
        object.__setattr__(self, "tolerance", tolerance)


@dataclass(frozen=True)
class ADPRecord:
    """Atomic displacement parameter record.

    Args:
        atom_id: Stable atom identifier.
        u_iso_angstrom2: Optional isotropic ``U`` value in square angstroms.
        b_iso_angstrom2: Optional isotropic ``B`` value in square angstroms.
        u_aniso_angstrom2: Optional ``(U11, U22, U33, U12, U13, U23)`` tuple.
    """

    atom_id: str
    u_iso_angstrom2: float | None = None
    b_iso_angstrom2: float | None = None
    u_aniso_angstrom2: tuple[float, float, float, float, float, float] | None = None

    def __post_init__(self) -> None:
        """Validate ADP identifiers and numeric fields."""
        if not isinstance(self.atom_id, str) or not self.atom_id:
            raise ValueError("ADPRecord.atom_id must be a non-empty string.")
        if self.u_iso_angstrom2 is not None:
            object.__setattr__(self, "u_iso_angstrom2", _finite_float(self.u_iso_angstrom2, "ADPRecord.u_iso_angstrom2"))
        if self.b_iso_angstrom2 is not None:
            object.__setattr__(self, "b_iso_angstrom2", _finite_float(self.b_iso_angstrom2, "ADPRecord.b_iso_angstrom2"))
        if self.u_aniso_angstrom2 is not None:
            values = tuple(_finite_float(value, f"ADPRecord.u_aniso_angstrom2[{index}]") for index, value in enumerate(self.u_aniso_angstrom2))
            if len(values) != 6:
                raise ValueError("ADPRecord.u_aniso_angstrom2 must contain six values.")
            object.__setattr__(self, "u_aniso_angstrom2", values)


def model_parameter_bounds(model_name: str) -> tuple[ModelParameterBounds, ...]:
    """Return parameter bounds for a startup diffraction model.

    Args:
        model_name: One of ``"preferred_orientation"``, ``"size_broadening"``,
            ``"strain_broadening"``, ``"polynomial_background"``, or
            ``"chebyshev_background"``.

    Returns:
        Deterministically ordered parameter bounds.

    Raises:
        ValueError: If ``model_name`` is empty.
        KeyError: If the model name is unsupported.
    """
    if not isinstance(model_name, str) or not model_name:
        raise ValueError("model_name must be a non-empty string.")
    bounds = {
        "preferred_orientation": (
            ModelParameterBounds("ratio", 0.1, 10.0, "dimensionless", "March-Dollase preferred-orientation ratio."),
            ModelParameterBounds("axis_component", -1.0, 1.0, "dimensionless", "Preferred-axis vector component."),
        ),
        "size_broadening": (
            ModelParameterBounds("crystallite_size_angstrom", 1.0, 1.0e12, "angstrom", "Isotropic Scherrer size proxy."),
            ModelParameterBounds("shape_factor", 0.01, 2.0, "dimensionless", "Scherrer shape factor."),
        ),
        "strain_broadening": (
            ModelParameterBounds("microstrain", 0.0, 1.0, "dimensionless", "Isotropic strain proxy."),
        ),
        "polynomial_background": (
            ModelParameterBounds("coefficient", -1.0e12, 1.0e12, "intensity", "Independent polynomial coefficient."),
            ModelParameterBounds("scale", 1.0e-12, 1.0e12, "axis unit", "Positive axis normalization scale."),
        ),
        "chebyshev_background": (
            ModelParameterBounds("coefficient", -1.0e12, 1.0e12, "intensity", "Independent Chebyshev coefficient."),
        ),
    }
    try:
        return bounds[model_name]
    except KeyError as exc:
        available = ", ".join(sorted(bounds))
        raise KeyError(f"Unsupported model_name {model_name!r}. Available models: {available}.") from exc


def preferred_orientation_factor(
    hkl: Sequence[int],
    preferred_axis: Sequence[float],
    *,
    ratio: float,
) -> float:
    """Return a March-Dollase-style preferred-orientation factor.

    This startup helper computes the angle between an ``hkl`` vector and a
    user-provided preferred axis in index space, then evaluates:

    ```text
    factor = (r^2 cos(alpha)^2 + sin(alpha)^2 / r)^(-3/2)
    ```

    Args:
        hkl: Three Miller indices.
        preferred_axis: Three finite vector components. The vector is
            normalized internally and must be non-zero.
        ratio: March-Dollase ratio bounded to ``[0.1, 10.0]``.

    Returns:
        Positive dimensionless intensity multiplier.

    Raises:
        ValueError: If indices, axis, or ratio are invalid.
    """
    miller = _validate_hkl(hkl, "hkl")
    axis = _normalized_vector(preferred_axis, "preferred_axis")
    ratio_value = _finite_float(ratio, "ratio")
    lower, upper = _PREFERRED_ORIENTATION_RATIO_BOUNDS
    if not lower <= ratio_value <= upper:
        raise ValueError(f"ratio must be between {lower} and {upper}, got {ratio_value!r}.")

    hkl_norm = math.sqrt(sum(float(index * index) for index in miller))
    hkl_unit = tuple(index / hkl_norm for index in miller)
    cos_alpha = abs(sum(component * axis_component for component, axis_component in zip(hkl_unit, axis, strict=True)))
    sin_alpha2 = max(0.0, 1.0 - cos_alpha * cos_alpha)
    denominator = ratio_value * ratio_value * cos_alpha * cos_alpha + sin_alpha2 / ratio_value
    return denominator ** -1.5


def isotropic_size_fwhm_degrees(
    two_theta_degrees: float,
    *,
    wavelength_angstrom: float,
    crystallite_size_angstrom: float,
    shape_factor: float = 0.9,
) -> float:
    """Return Scherrer isotropic-size broadening in degrees two-theta.

    Args:
        two_theta_degrees: Peak position in degrees two-theta, on ``(0, 180)``.
        wavelength_angstrom: Radiation wavelength in angstroms. Must be
            positive.
        crystallite_size_angstrom: Isotropic crystallite-size proxy in
            angstroms. Must be positive.
        shape_factor: Positive Scherrer shape factor.

    Returns:
        Full width at half maximum in degrees two-theta.

    Raises:
        ValueError: If any input is non-finite or outside its bounds.
    """
    theta = _theta_radians(two_theta_degrees)
    wavelength = _positive_float(wavelength_angstrom, "wavelength_angstrom")
    size = _positive_float(crystallite_size_angstrom, "crystallite_size_angstrom")
    shape = _positive_float(shape_factor, "shape_factor")
    return math.degrees(shape * wavelength / (size * math.cos(theta)))


def isotropic_strain_fwhm_degrees(two_theta_degrees: float, *, microstrain: float) -> float:
    """Return isotropic strain broadening in degrees two-theta.

    The startup expression is ``beta = 4 * microstrain * tan(theta)`` in
    radians.

    Args:
        two_theta_degrees: Peak position in degrees two-theta, on ``(0, 180)``.
        microstrain: Non-negative dimensionless strain proxy.

    Returns:
        Full width at half maximum in degrees two-theta.

    Raises:
        ValueError: If any input is non-finite or outside its bounds.
    """
    theta = _theta_radians(two_theta_degrees)
    strain = _finite_float(microstrain, "microstrain")
    if strain < 0.0:
        raise ValueError(f"microstrain must be non-negative, got {strain!r}.")
    return math.degrees(4.0 * strain * math.tan(theta))


def polynomial_background(
    x: Sequence[float],
    coefficients: Sequence[float],
    *,
    origin: float = 0.0,
    scale: float = 1.0,
) -> list[float]:
    """Evaluate an independently refinable polynomial background.

    Args:
        x: Axis values.
        coefficients: Polynomial coefficients ordered from degree zero upward.
        origin: Axis origin subtracted before evaluation.
        scale: Positive axis normalization scale.

    Returns:
        Background intensity values.

    Raises:
        ValueError: If inputs are malformed or non-finite.
    """
    axis = _finite_sequence(x, "x")
    coeffs = _finite_sequence(coefficients, "coefficients")
    origin_value = _finite_float(origin, "origin")
    scale_value = _positive_float(scale, "scale")
    values: list[float] = []
    for axis_value in axis:
        normalized = (axis_value - origin_value) / scale_value
        total = 0.0
        power = 1.0
        for coefficient in coeffs:
            total += coefficient * power
            power *= normalized
        values.append(total)
    return values


def chebyshev_background(
    x: Sequence[float],
    coefficients: Sequence[float],
    *,
    domain: tuple[float, float],
) -> list[float]:
    """Evaluate a Chebyshev background on a finite axis domain.

    Args:
        x: Axis values.
        coefficients: Chebyshev coefficients ordered from ``T0`` upward.
        domain: ``(min, max)`` domain used to map ``x`` into ``[-1, 1]``.

    Returns:
        Background intensity values.

    Raises:
        ValueError: If inputs are malformed or the domain is invalid.
    """
    axis = _finite_sequence(x, "x")
    coeffs = _finite_sequence(coefficients, "coefficients")
    domain_min, domain_max = _finite_pair(domain, "domain")
    if domain_min >= domain_max:
        raise ValueError("domain minimum must be less than domain maximum.")
    return [_evaluate_chebyshev_terms(_map_to_unit_domain(axis_value, domain_min, domain_max), coeffs) for axis_value in axis]


def generate_reflection_ticks(
    reflections: Sequence[SyntheticReflection],
    *,
    two_theta_range: tuple[float, float] | None = None,
) -> tuple[ReflectionTick, ...]:
    """Generate sorted reflection ticks for synthetic display payloads.

    Args:
        reflections: Synthetic reflections to convert to ticks.
        two_theta_range: Optional inclusive ``(min, max)`` filter in degrees
            two-theta.

    Returns:
        Reflection ticks sorted by position, phase, and label.

    Raises:
        ValueError: If inputs or range are invalid.
    """
    lower = -math.inf
    upper = math.inf
    if two_theta_range is not None:
        lower, upper = _finite_pair(two_theta_range, "two_theta_range")
        if lower > upper:
            raise ValueError("two_theta_range minimum must not exceed maximum.")
    ticks: list[ReflectionTick] = []
    for index, reflection in enumerate(reflections):
        if not isinstance(reflection, SyntheticReflection):
            raise ValueError(f"reflections[{index}] must be a SyntheticReflection.")
        if lower <= reflection.two_theta_degrees <= upper:
            label = _format_hkl_label(reflection.hkl)
            ticks.append(
                ReflectionTick(
                    phase_id=reflection.phase_id,
                    hkl=reflection.hkl,
                    two_theta_degrees=reflection.two_theta_degrees,
                    label=label,
                    intensity=reflection.intensity,
                )
            )
    return tuple(sorted(ticks, key=lambda tick: (tick.two_theta_degrees, tick.phase_id, tick.label)))


def generate_synthetic_pattern(
    axis_two_theta_degrees: Sequence[float],
    reflections: Sequence[SyntheticReflection],
    *,
    background: Sequence[float] | None = None,
    phase_scales: Mapping[str, float] | None = None,
) -> SyntheticPattern:
    """Generate a deterministic synthetic powder pattern.

    Peaks are area-normalized Gaussian profiles in degrees two-theta. The
    returned metadata records that the pattern is synthetic and identifies the
    startup assumptions.

    Args:
        axis_two_theta_degrees: Sorted pattern axis in degrees two-theta.
        reflections: Synthetic reflection inputs.
        background: Optional background values with the same length as the
            axis. Missing background defaults to zeros.
        phase_scales: Optional non-negative phase scale multipliers.

    Returns:
        Synthetic pattern values, reflection ticks, and metadata.

    Raises:
        ValueError: If axes, reflections, background, or scales are invalid.
    """
    axis = _finite_sequence(axis_two_theta_degrees, "axis_two_theta_degrees")
    _require_sorted(axis, "axis_two_theta_degrees")
    reflected = _validate_reflections(reflections)
    if background is None:
        intensities = [0.0 for _ in axis]
    else:
        intensities = _finite_sequence(background, "background")
        if len(intensities) != len(axis):
            raise ValueError("background length must match axis_two_theta_degrees length.")
    scales = _validate_phase_scales(phase_scales)

    for reflection in reflected:
        phase_scale = scales.get(reflection.phase_id, 1.0)
        area = reflection.intensity * phase_scale
        profile = _gaussian_profile(axis, center=reflection.two_theta_degrees, fwhm=reflection.fwhm_degrees, area=area)
        intensities = [current + addition for current, addition in zip(intensities, profile, strict=True)]

    if axis:
        axis_min = str(axis[0])
        axis_max = str(axis[-1])
    else:
        axis_min = ""
        axis_max = ""
    metadata = {
        "generator": _SYNTHETIC_GENERATOR_VERSION,
        "axis_unit": "degrees two-theta",
        "profile": "area-normalized Gaussian",
        "background": "provided values" if background is not None else "zero",
        "axis_min": axis_min,
        "axis_max": axis_max,
        "assumption": "synthetic startup pattern; no measured validation data implied",
    }
    return SyntheticPattern(
        axis_two_theta_degrees=tuple(axis),
        intensity=tuple(intensities),
        phase_ticks=generate_reflection_ticks(reflected),
        metadata=metadata,
    )


def standard_reference_dataset_registry() -> tuple[StandardReferenceDataset, ...]:
    """Return deterministic startup reference dataset registry entries.

    Returns:
        Registry entries. Current entries are synthetic placeholders and record
        their validation status explicitly.
    """
    return (
        StandardReferenceDataset(
            dataset_id="synthetic-si-powder-v0",
            title="Synthetic cubic silicon powder startup fixture",
            category="synthetic-powder",
            axis_unit="degrees two-theta",
            source="rietveld_next.diffraction.models",
            validation_status="synthetic-only",
            notes="Deterministic placeholder for API tests; not measured reference data.",
        ),
        StandardReferenceDataset(
            dataset_id="synthetic-two-phase-v0",
            title="Synthetic two-phase powder startup fixture",
            category="synthetic-powder",
            axis_unit="degrees two-theta",
            source="rietveld_next.diffraction.models",
            validation_status="synthetic-only",
            notes="Deterministic placeholder for phase-fraction and tick tests.",
        ),
    )


def lookup_standard_reference_dataset(dataset_id: str) -> StandardReferenceDataset:
    """Look up a startup reference dataset registry entry.

    Args:
        dataset_id: Stable dataset identifier.

    Returns:
        Matching registry entry.

    Raises:
        ValueError: If ``dataset_id`` is empty.
        KeyError: If no entry exists.
    """
    if not isinstance(dataset_id, str) or not dataset_id:
        raise ValueError("dataset_id must be a non-empty string.")
    registry = {entry.dataset_id: entry for entry in standard_reference_dataset_registry()}
    try:
        return registry[dataset_id]
    except KeyError as exc:
        available = ", ".join(sorted(registry))
        raise KeyError(f"Unsupported dataset_id {dataset_id!r}. Available datasets: {available}.") from exc


def phase_scale_weight(component: PhaseScaleComponent) -> float:
    """Return the unnormalized startup phase weight proxy.

    Args:
        component: Validated phase scale component.

    Returns:
        Non-negative weight proxy used by :func:`calculate_phase_fractions`.

    Raises:
        TypeError: If ``component`` has the wrong type.
    """
    if not isinstance(component, PhaseScaleComponent):
        raise TypeError("component must be a PhaseScaleComponent.")
    return (
        component.scale
        * component.formula_units_per_cell
        * component.molecular_mass_g_mol
        * component.cell_volume_angstrom3
    )


def calculate_phase_fractions(components: Sequence[PhaseScaleComponent]) -> PhaseFractionResult:
    """Normalize startup phase scale components to fractions.

    The calculation assumes all components use the same global scale
    convention and applies the documented proxy in
    :class:`PhaseScaleComponent`. Fractions are normalized by the sum of
    positive weight proxies.

    Args:
        components: Phase scale components.

    Returns:
        Fractions, unnormalized weights, and assumptions.

    Raises:
        ValueError: If phase IDs are duplicated, no components are supplied, or
            all weights are zero.
    """
    if isinstance(components, str) or not isinstance(components, Sequence) or not components:
        raise ValueError("components must be a non-empty sequence of PhaseScaleComponent records.")
    weights: dict[str, float] = {}
    for index, component in enumerate(components):
        if not isinstance(component, PhaseScaleComponent):
            raise ValueError(f"components[{index}] must be a PhaseScaleComponent.")
        if component.phase_id in weights:
            raise ValueError(f"Duplicate phase_id {component.phase_id!r}.")
        weights[component.phase_id] = phase_scale_weight(component)
    total = sum(weights.values())
    if total <= 0.0:
        raise ValueError("At least one phase scale weight must be positive.")
    fractions = {phase_id: weight / total for phase_id, weight in weights.items()}
    assumptions = (
        "weight_proxy = scale * formula_units_per_cell * molecular_mass_g_mol * cell_volume_angstrom3",
        "fractions are normalized by the sum of startup weight proxies",
        "synthetic helper only; no absorption or preferred-orientation correction is applied",
    )
    return PhaseFractionResult(fractions=fractions, weights=weights, assumptions=assumptions)


def validate_occupancy_constraints(
    sites: Sequence[OccupancySite],
    constraints: Sequence[OccupancyConstraint],
) -> tuple[StructuredWarning, ...]:
    """Validate simple atom occupancy bounds and linear constraints.

    Args:
        sites: Atom occupancy records.
        constraints: Linear occupancy constraints to evaluate.

    Returns:
        Structured warnings for out-of-range occupancies, missing sites,
        duplicates, and constraint-sum mismatches.

    Raises:
        ValueError: If inputs contain unsupported record types.
    """
    site_map: dict[str, OccupancySite] = {}
    warnings: list[StructuredWarning] = []
    for index, site in enumerate(sites):
        if not isinstance(site, OccupancySite):
            raise ValueError(f"sites[{index}] must be an OccupancySite.")
        if site.site_id in site_map:
            warnings.append(
                StructuredWarning(
                    code="occupancy.duplicate_site",
                    message=f"Duplicate occupancy site {site.site_id!r}.",
                    path=f"sites[{index}].site_id",
                    severity="error",
                )
            )
        site_map[site.site_id] = site
        if not 0.0 <= site.occupancy <= 1.0:
            warnings.append(
                StructuredWarning(
                    code="occupancy.out_of_bounds",
                    message=f"Occupancy for site {site.site_id!r} is outside [0, 1].",
                    path=f"sites.{site.site_id}.occupancy",
                    severity="error",
                    value=site.occupancy,
                    bounds=(0.0, 1.0),
                )
            )

    for index, constraint in enumerate(constraints):
        if not isinstance(constraint, OccupancyConstraint):
            raise ValueError(f"constraints[{index}] must be an OccupancyConstraint.")
        missing = [site_id for site_id in constraint.site_ids if site_id not in site_map]
        for site_id in missing:
            warnings.append(
                StructuredWarning(
                    code="occupancy.missing_site",
                    message=f"Constraint {constraint.constraint_id!r} references missing site {site_id!r}.",
                    path=f"constraints.{constraint.constraint_id}.site_ids",
                    severity="error",
                )
            )
        if missing:
            continue
        total = sum(site_map[site_id].occupancy for site_id in constraint.site_ids)
        delta = abs(total - constraint.target_total)
        if delta > constraint.tolerance:
            warnings.append(
                StructuredWarning(
                    code="occupancy.constraint_mismatch",
                    message=(
                        f"Constraint {constraint.constraint_id!r} sum {total!r} differs from "
                        f"target {constraint.target_total!r} by more than {constraint.tolerance!r}."
                    ),
                    path=f"constraints.{constraint.constraint_id}.target_total",
                    severity="warning",
                    value=total,
                    bounds=(constraint.target_total - constraint.tolerance, constraint.target_total + constraint.tolerance),
                )
            )
    return tuple(warnings)


def validate_adp_records(
    records: Sequence[ADPRecord],
    *,
    u_iso_bounds_angstrom2: tuple[float, float] = (0.0, _DEFAULT_ADP_U_MAX_ANGSTROM2),
    tolerance: float = _DEFAULT_TOLERANCE,
) -> tuple[StructuredWarning, ...]:
    """Validate isotropic and anisotropic ADP records.

    Args:
        records: ADP records to check.
        u_iso_bounds_angstrom2: Inclusive expected ``U`` bounds. ``B`` values
            are converted with ``B = 8*pi^2*U`` before comparison.
        tolerance: Positive-definite matrix tolerance for anisotropic ``U``.

    Returns:
        Structured warnings. Negative values and non-positive-definite
        anisotropic matrices are reported as ``"error"``.

    Raises:
        ValueError: If inputs or validation bounds are malformed.
    """
    lower, upper = _finite_pair(u_iso_bounds_angstrom2, "u_iso_bounds_angstrom2")
    if lower < 0.0 or lower > upper:
        raise ValueError("u_iso_bounds_angstrom2 must be ordered and non-negative.")
    tolerance_value = _finite_float(tolerance, "tolerance")
    if tolerance_value < 0.0:
        raise ValueError(f"tolerance must be non-negative, got {tolerance_value!r}.")

    warnings: list[StructuredWarning] = []
    seen: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, ADPRecord):
            raise ValueError(f"records[{index}] must be an ADPRecord.")
        if record.atom_id in seen:
            warnings.append(
                StructuredWarning(
                    code="adp.duplicate_atom",
                    message=f"Duplicate ADP atom {record.atom_id!r}.",
                    path=f"records[{index}].atom_id",
                    severity="error",
                )
            )
        seen.add(record.atom_id)
        if record.u_iso_angstrom2 is None and record.b_iso_angstrom2 is None and record.u_aniso_angstrom2 is None:
            warnings.append(
                StructuredWarning(
                    code="adp.missing",
                    message=f"Atom {record.atom_id!r} has no ADP values.",
                    path=f"records.{record.atom_id}",
                    severity="warning",
                )
            )
        if record.u_iso_angstrom2 is not None:
            _append_u_bound_warning(
                warnings,
                value=record.u_iso_angstrom2,
                bounds=(lower, upper),
                path=f"records.{record.atom_id}.u_iso_angstrom2",
                code_prefix="adp.u_iso",
            )
        if record.b_iso_angstrom2 is not None:
            converted_u = record.b_iso_angstrom2 / (8.0 * math.pi * math.pi)
            _append_u_bound_warning(
                warnings,
                value=converted_u,
                bounds=(lower, upper),
                path=f"records.{record.atom_id}.b_iso_angstrom2",
                code_prefix="adp.b_iso_as_u",
            )
        if record.u_aniso_angstrom2 is not None:
            _append_anisotropic_adp_warnings(
                warnings,
                atom_id=record.atom_id,
                values=record.u_aniso_angstrom2,
                bounds=(lower, upper),
                tolerance=tolerance_value,
            )
    return tuple(warnings)


def _append_u_bound_warning(
    warnings: list[StructuredWarning],
    *,
    value: float,
    bounds: tuple[float, float],
    path: str,
    code_prefix: str,
) -> None:
    lower, upper = bounds
    if value < lower:
        warnings.append(
            StructuredWarning(
                code=f"{code_prefix}.negative",
                message=f"ADP value {value!r} is below the lower bound {lower!r}.",
                path=path,
                severity="error",
                value=value,
                bounds=bounds,
            )
        )
    elif value > upper:
        warnings.append(
            StructuredWarning(
                code=f"{code_prefix}.high",
                message=f"ADP value {value!r} is above the upper review bound {upper!r}.",
                path=path,
                severity="warning",
                value=value,
                bounds=bounds,
            )
        )


def _append_anisotropic_adp_warnings(
    warnings: list[StructuredWarning],
    *,
    atom_id: str,
    values: tuple[float, float, float, float, float, float],
    bounds: tuple[float, float],
    tolerance: float,
) -> None:
    u11, u22, u33, u12, u13, u23 = values
    for label, value in zip(("U11", "U22", "U33"), (u11, u22, u33), strict=True):
        _append_u_bound_warning(
            warnings,
            value=value,
            bounds=bounds,
            path=f"records.{atom_id}.u_aniso_angstrom2.{label}",
            code_prefix=f"adp.u_aniso.{label.lower()}",
        )
    determinant_2 = u11 * u22 - u12 * u12
    determinant_3 = (
        u11 * (u22 * u33 - u23 * u23)
        - u12 * (u12 * u33 - u13 * u23)
        + u13 * (u12 * u23 - u13 * u22)
    )
    if u11 <= tolerance or determinant_2 <= tolerance or determinant_3 <= tolerance:
        warnings.append(
            StructuredWarning(
                code="adp.u_aniso.not_positive_definite",
                message=f"Anisotropic ADP matrix for atom {atom_id!r} is not positive definite within tolerance.",
                path=f"records.{atom_id}.u_aniso_angstrom2",
                severity="error",
            )
        )


def _validate_reflections(reflections: Sequence[SyntheticReflection]) -> tuple[SyntheticReflection, ...]:
    if isinstance(reflections, str) or not isinstance(reflections, Sequence):
        raise ValueError("reflections must be a sequence of SyntheticReflection records.")
    validated: list[SyntheticReflection] = []
    for index, reflection in enumerate(reflections):
        if not isinstance(reflection, SyntheticReflection):
            raise ValueError(f"reflections[{index}] must be a SyntheticReflection.")
        validated.append(reflection)
    return tuple(validated)


def _validate_phase_scales(phase_scales: Mapping[str, float] | None) -> dict[str, float]:
    if phase_scales is None:
        return {}
    if not isinstance(phase_scales, Mapping):
        raise ValueError("phase_scales must be a mapping from phase_id to non-negative finite scale.")
    scales: dict[str, float] = {}
    for phase_id, scale in phase_scales.items():
        if not isinstance(phase_id, str) or not phase_id:
            raise ValueError("phase_scales keys must be non-empty phase identifiers.")
        scale_value = _finite_float(scale, f"phase_scales[{phase_id!r}]")
        if scale_value < 0.0:
            raise ValueError(f"phase_scales[{phase_id!r}] must be non-negative, got {scale_value!r}.")
        scales[phase_id] = scale_value
    return scales


def _gaussian_profile(x: Sequence[float], *, center: float, fwhm: float, area: float) -> list[float]:
    scale = area * _GAUSSIAN_NORMALIZATION / fwhm
    return [scale * math.exp(-_GAUSSIAN_LOG2_FACTOR * ((axis_value - center) / fwhm) ** 2) for axis_value in x]


def _theta_radians(two_theta_degrees: float) -> float:
    two_theta = _finite_float(two_theta_degrees, "two_theta_degrees")
    if not 0.0 < two_theta < 180.0:
        raise ValueError(f"two_theta_degrees must be between 0 and 180 degrees, got {two_theta!r}.")
    return math.radians(0.5 * two_theta)


def _positive_float(value: float, name: str) -> float:
    numeric = _finite_float(value, name)
    if numeric <= 0.0:
        raise ValueError(f"{name} must be positive, got {numeric!r}.")
    return numeric


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _finite_sequence(values: Sequence[float], name: str) -> list[float]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    return [_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values)]


def _finite_pair(values: Sequence[float], name: str) -> tuple[float, float]:
    if isinstance(values, str) or not isinstance(values, Sequence) or len(values) != 2:
        raise ValueError(f"{name} must be a two-item sequence of finite numbers.")
    return (_finite_float(values[0], f"{name}[0]"), _finite_float(values[1], f"{name}[1]"))


def _validate_hkl(hkl: Sequence[int], name: str) -> tuple[int, int, int]:
    if isinstance(hkl, str) or not isinstance(hkl, Sequence) or len(hkl) != 3:
        raise ValueError(f"{name} must be a three-item sequence of integers.")
    indices: list[int] = []
    for axis_name, value in zip(("h", "k", "l"), hkl, strict=True):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name}.{axis_name} must be an integer, got {value!r}.")
        indices.append(value)
    if indices == [0, 0, 0]:
        raise ValueError(f"{name} must not be (0, 0, 0).")
    return indices[0], indices[1], indices[2]


def _normalized_vector(values: Sequence[float], name: str) -> tuple[float, float, float]:
    vector = _finite_sequence(values, name)
    if len(vector) != 3:
        raise ValueError(f"{name} must contain exactly three components.")
    norm = math.sqrt(sum(component * component for component in vector))
    if norm == 0.0:
        raise ValueError(f"{name} must be non-zero.")
    return (vector[0] / norm, vector[1] / norm, vector[2] / norm)


def _require_sorted(values: Sequence[float], name: str) -> None:
    for index, (left, right) in enumerate(zip(values, values[1:], strict=False)):
        if right < left:
            raise ValueError(f"{name} must be sorted in non-decreasing order; item {index + 1} is out of order.")


def _evaluate_chebyshev_terms(x: float, coefficients: Sequence[float]) -> float:
    if not coefficients:
        return 0.0
    if len(coefficients) == 1:
        return coefficients[0]
    total = coefficients[0] + coefficients[1] * x
    previous = 1.0
    current = x
    for coefficient in coefficients[2:]:
        next_value = 2.0 * x * current - previous
        total += coefficient * next_value
        previous = current
        current = next_value
    return total


def _map_to_unit_domain(value: float, domain_min: float, domain_max: float) -> float:
    return 2.0 * (value - domain_min) / (domain_max - domain_min) - 1.0


def _format_hkl_label(hkl: tuple[int, int, int]) -> str:
    return f"({hkl[0]} {hkl[1]} {hkl[2]})"


__all__ = [
    "ADPRecord",
    "ModelParameterBounds",
    "OccupancyConstraint",
    "OccupancySite",
    "PhaseFractionResult",
    "PhaseScaleComponent",
    "ReflectionTick",
    "StandardReferenceDataset",
    "StructuredWarning",
    "SyntheticPattern",
    "SyntheticReflection",
    "calculate_phase_fractions",
    "chebyshev_background",
    "generate_reflection_ticks",
    "generate_synthetic_pattern",
    "isotropic_size_fwhm_degrees",
    "isotropic_strain_fwhm_degrees",
    "lookup_standard_reference_dataset",
    "model_parameter_bounds",
    "phase_scale_weight",
    "polynomial_background",
    "preferred_orientation_factor",
    "standard_reference_dataset_registry",
    "validate_adp_records",
    "validate_occupancy_constraints",
]
