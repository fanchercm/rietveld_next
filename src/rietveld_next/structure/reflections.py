"""Deterministic startup reflection generation."""

from __future__ import annotations

from dataclasses import dataclass
import math

from rietveld_next.structure.models import UnitCell
from rietveld_next.structure.symmetry import lookup_space_group


@dataclass(frozen=True)
class Reflection:
    """Generated reflection record.

    Args:
        h: Miller index h.
        k: Miller index k.
        l: Miller index l.
        d_spacing_angstrom: Plane spacing in angstroms.
        multiplicity: Startup multiplicity. P1 currently emits 1.
    """

    h: int
    k: int
    l: int
    d_spacing_angstrom: float
    multiplicity: int = 1

    def __post_init__(self) -> None:
        """Validate generated reflection values."""
        if (self.h, self.k, self.l) == (0, 0, 0):
            raise ValueError("Reflection (0, 0, 0) is not physical.")
        if not isinstance(self.multiplicity, int) or self.multiplicity <= 0:
            raise ValueError("Reflection multiplicity must be a positive integer.")
        if not isinstance(self.d_spacing_angstrom, int | float) or not math.isfinite(self.d_spacing_angstrom):
            raise ValueError("Reflection d_spacing_angstrom must be finite.")
        if self.d_spacing_angstrom <= 0.0:
            raise ValueError("Reflection d_spacing_angstrom must be positive.")


def generate_reflections(
    cell: UnitCell,
    space_group: str | int,
    *,
    max_index: int,
) -> tuple[Reflection, ...]:
    """Generate deterministic startup reflections.

    Args:
        cell: Unit cell used for d-spacing calculation.
        space_group: Supported space-group identifier. Only P1 currently has
            operation support.
        max_index: Inclusive absolute Miller-index bound.

    Returns:
        Reflections sorted by increasing ``1 / d^2`` and then Miller index.

    Raises:
        ValueError: If the space group lacks operation support or inputs are
            invalid.
    """
    if not isinstance(cell, UnitCell):
        raise TypeError("cell must be a UnitCell.")
    if not isinstance(max_index, int) or isinstance(max_index, bool) or max_index < 1:
        raise ValueError("max_index must be a positive integer.")
    info = lookup_space_group(space_group)
    if not info.supported_operations:
        raise ValueError(f"Reflection generation is not implemented for space group {info.hermann_mauguin}.")
    reflections: list[Reflection] = []
    for h in range(-max_index, max_index + 1):
        for k in range(-max_index, max_index + 1):
            for l in range(-max_index, max_index + 1):
                if (h, k, l) == (0, 0, 0):
                    continue
                reflections.append(Reflection(h, k, l, _d_spacing(cell, h, k, l)))
    return tuple(sorted(reflections, key=lambda reflection: (1.0 / reflection.d_spacing_angstrom**2, reflection.h, reflection.k, reflection.l)))


def _d_spacing(cell: UnitCell, h: int, k: int, l: int) -> float:
    alpha = math.radians(cell.alpha)
    beta = math.radians(cell.beta)
    gamma = math.radians(cell.gamma)
    cos_alpha = math.cos(alpha)
    cos_beta = math.cos(beta)
    cos_gamma = math.cos(gamma)
    sin_alpha = math.sin(alpha)
    sin_beta = math.sin(beta)
    sin_gamma = math.sin(gamma)
    volume = cell.volume_angstrom3
    astar = cell.b * cell.c * sin_alpha / volume
    bstar = cell.a * cell.c * sin_beta / volume
    cstar = cell.a * cell.b * sin_gamma / volume
    cos_alpha_star = (cos_beta * cos_gamma - cos_alpha) / (sin_beta * sin_gamma)
    cos_beta_star = (cos_alpha * cos_gamma - cos_beta) / (sin_alpha * sin_gamma)
    cos_gamma_star = (cos_alpha * cos_beta - cos_gamma) / (sin_alpha * sin_beta)
    inverse_d2 = (
        h * h * astar * astar
        + k * k * bstar * bstar
        + l * l * cstar * cstar
        + 2.0 * h * k * astar * bstar * cos_gamma_star
        + 2.0 * h * l * astar * cstar * cos_beta_star
        + 2.0 * k * l * bstar * cstar * cos_alpha_star
    )
    if inverse_d2 <= 0.0:
        raise ValueError(f"Cell geometry produced non-positive reciprocal spacing for {(h, k, l)}.")
    return 1.0 / math.sqrt(inverse_d2)
