"""Magnetic symmetry constraint records for the parameter graph."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import math
from typing import Any

from rietveld_next.core.model import Constraint, ConstraintKind, ParameterPath


MAGNETIC_MOMENT_COMPONENTS = frozenset({"mx", "my", "mz"})


@dataclass(frozen=True)
class MagneticSymmetryConstraint:
    """Symbolic magnetic moment constraint represented in the parameter graph.

    Args:
        constraint_id: Stable constraint identifier.
        parameter_ids: Refinement parameter IDs referenced by the expression.
        expression: Symbolic expression using the referenced parameter IDs.
        operation_label: Magnetic symmetry operation or site relation label.
        units: Units for constrained moment components.
        metadata: Optional deterministic provenance metadata.

    Raises:
        ValueError: If identifiers, expression, units, or metadata keys are invalid.

    Example:
        >>> c = MagneticSymmetryConstraint("c_mx", ("m1_mx", "m2_mx"), "m2_mx = -m1_mx", "m_x flip")
        >>> c.to_core_constraint().kind.value
        'symbolic'
    """

    constraint_id: str
    parameter_ids: tuple[str, ...]
    expression: str
    operation_label: str
    units: str = "bohr_magneton"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate symbolic relation metadata."""

        _non_empty_string(self.constraint_id, "constraint_id")
        _non_empty_string(self.expression, "expression")
        _non_empty_string(self.operation_label, "operation_label")
        if self.units != "bohr_magneton":
            raise ValueError("units must be 'bohr_magneton' for magnetic moment constraints.")
        if isinstance(self.parameter_ids, str) or not isinstance(self.parameter_ids, Sequence):
            raise ValueError("parameter_ids must be a sequence of parameter IDs.")
        parameter_ids = tuple(_non_empty_string(value, "parameter_ids") for value in self.parameter_ids)
        if not parameter_ids:
            raise ValueError("parameter_ids must not be empty.")
        metadata = _metadata_dict(self.metadata)
        object.__setattr__(self, "parameter_ids", parameter_ids)
        object.__setattr__(self, "metadata", metadata)

    def to_core_constraint(self) -> Constraint:
        """Convert to the shared core-model constraint record."""

        return Constraint(
            id=self.constraint_id,
            kind=ConstraintKind.SYMBOLIC,
            expression=self.expression,
            parameter_ids=list(self.parameter_ids),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible representation."""

        return {
            "constraint_id": self.constraint_id,
            "kind": "magnetic_symmetry",
            "parameter_ids": list(self.parameter_ids),
            "expression": self.expression,
            "operation_label": self.operation_label,
            "units": self.units,
            "metadata": dict(sorted(self.metadata.items())),
        }


def magnetic_moment_parameter_path(
    phase_id: str,
    site_id: str,
    component: str,
) -> ParameterPath:
    """Return the canonical parameter path for a magnetic moment component.

    Args:
        phase_id: Owning phase ID.
        site_id: Magnetic atom-site ID.
        component: Moment component, one of ``mx``, ``my``, or ``mz``.

    Returns:
        Core-model parameter path under ``phase/<phase_id>/magnetic_structure``.

    Raises:
        ValueError: If ``component`` is unsupported.

    Example:
        >>> str(magnetic_moment_parameter_path("phase1", "mn1", "mz"))
        'phase/phase1/magnetic_structure/sites/mn1/moment/mz'
    """

    _non_empty_string(phase_id, "phase_id")
    _non_empty_string(site_id, "site_id")
    normalized_component = _moment_component(component)
    return ParameterPath(
        "phase",
        phase_id,
        ("magnetic_structure", "sites", site_id, "moment", normalized_component),
    )


def magnetic_moment_parameter_id(
    phase_id: str,
    site_id: str,
    component: str,
) -> str:
    """Return a stable parameter ID for a magnetic moment component."""

    path = magnetic_moment_parameter_path(phase_id, site_id, component)
    return "p_" + str(path).replace("/", "_")


def create_collinear_moment_constraint(
    *,
    constraint_id: str,
    phase_id: str,
    reference_site_id: str,
    constrained_site_id: str,
    component: str,
    multiplier: float,
    operation_label: str,
) -> MagneticSymmetryConstraint:
    """Create a symbolic constraint tying two site moment components.

    Args:
        constraint_id: Stable constraint identifier.
        phase_id: Owning phase ID.
        reference_site_id: Site whose component is the independent value.
        constrained_site_id: Site whose component is constrained.
        component: Moment component, one of ``mx``, ``my``, or ``mz``.
        multiplier: Finite scalar relation ``constrained = multiplier * reference``.
        operation_label: Magnetic symmetry operation label.

    Returns:
        Magnetic symmetry constraint that can be converted to a core constraint.

    Raises:
        ValueError: If any identifier, component, or multiplier is invalid.
    """

    if isinstance(multiplier, bool) or not isinstance(multiplier, int | float) or not math.isfinite(multiplier):
        raise ValueError("multiplier must be a finite number.")
    component_name = _moment_component(component)
    reference_id = magnetic_moment_parameter_id(phase_id, reference_site_id, component_name)
    constrained_id = magnetic_moment_parameter_id(phase_id, constrained_site_id, component_name)
    return MagneticSymmetryConstraint(
        constraint_id=constraint_id,
        parameter_ids=(constrained_id, reference_id),
        expression=f"{constrained_id} = {float(multiplier):.12g} * {reference_id}",
        operation_label=operation_label,
        metadata={
            "component": component_name,
            "constrained_site_id": constrained_site_id,
            "phase_id": phase_id,
            "reference_site_id": reference_site_id,
        },
    )


def _moment_component(component: str) -> str:
    value = _non_empty_string(component, "component").lower()
    if value not in MAGNETIC_MOMENT_COMPONENTS:
        allowed = ", ".join(sorted(MAGNETIC_MOMENT_COMPONENTS))
        raise ValueError(f"component must be one of: {allowed}.")
    return value


def _metadata_dict(metadata: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(metadata, Mapping):
        raise ValueError("metadata must be a mapping.")
    normalized = {}
    for key, value in metadata.items():
        if not isinstance(key, str) or not key:
            raise ValueError("metadata keys must be non-empty strings.")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"metadata value for {key!r} must be finite.")
        normalized[key] = value
    return dict(sorted(normalized.items()))


def _non_empty_string(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value
