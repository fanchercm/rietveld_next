"""Typed structural records for CIF import and reflection utilities.

The records in this package intentionally cover a small crystallographic
baseline. Lengths use angstroms, angles use degrees, and fractional atom
coordinates are unitless fractions of the direct unit cell.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class UnitCell:
    """A crystallographic unit cell with explicit units.

    Args:
        a: Cell length ``a`` in angstroms. Must be positive and finite.
        b: Cell length ``b`` in angstroms. Must be positive and finite.
        c: Cell length ``c`` in angstroms. Must be positive and finite.
        alpha: Cell angle alpha in degrees. Must be in ``(0, 180)``.
        beta: Cell angle beta in degrees. Must be in ``(0, 180)``.
        gamma: Cell angle gamma in degrees. Must be in ``(0, 180)``.

    Raises:
        ValueError: If any length, angle, or implied volume is invalid.

    Example:
        >>> UnitCell(1.0, 1.0, 1.0, 90.0, 90.0, 90.0).volume_angstrom3
        1.0
    """

    a: float
    b: float
    c: float
    alpha: float
    beta: float
    gamma: float

    def __post_init__(self) -> None:
        for field_name in ("a", "b", "c"):
            value = _finite_float(getattr(self, field_name), f"UnitCell.{field_name}")
            if value <= 0.0:
                raise ValueError(f"UnitCell.{field_name} must be positive angstroms, got {value!r}.")
            object.__setattr__(self, field_name, value)
        for field_name in ("alpha", "beta", "gamma"):
            value = _finite_float(getattr(self, field_name), f"UnitCell.{field_name}")
            if value <= 0.0 or value >= 180.0:
                raise ValueError(f"UnitCell.{field_name} must be between 0 and 180 degrees, got {value!r}.")
            object.__setattr__(self, field_name, value)
        if self.volume_angstrom3 <= 0.0:
            raise ValueError("UnitCell angles imply a non-positive cell volume.")

    @property
    def volume_angstrom3(self) -> float:
        """Return the direct-cell volume in cubic angstroms."""
        alpha_rad = math.radians(self.alpha)
        beta_rad = math.radians(self.beta)
        gamma_rad = math.radians(self.gamma)
        cos_alpha = math.cos(alpha_rad)
        cos_beta = math.cos(beta_rad)
        cos_gamma = math.cos(gamma_rad)
        volume_factor = math.sqrt(
            max(
                0.0,
                1.0
                - cos_alpha**2
                - cos_beta**2
                - cos_gamma**2
                + 2.0 * cos_alpha * cos_beta * cos_gamma,
            )
        )
        return self.a * self.b * self.c * volume_factor


@dataclass(frozen=True)
class AtomSite:
    """A fractional atom-site record parsed from CIF atom-site loops.

    Args:
        label: Site label from ``_atom_site_label``.
        type_symbol: Element/type symbol from ``_atom_site_type_symbol`` when
            present. If omitted in CIF v0, the label is used as a conservative
            placeholder.
        fract_x: Fractional x coordinate. Must be finite.
        fract_y: Fractional y coordinate. Must be finite.
        fract_z: Fractional z coordinate. Must be finite.
        occupancy: Optional finite occupancy on ``[0, 1]``.

    Raises:
        ValueError: If identifiers are empty or numeric values are invalid.
    """

    label: str
    type_symbol: str
    fract_x: float
    fract_y: float
    fract_z: float
    occupancy: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.label, str) or not self.label:
            raise ValueError("AtomSite.label must be a non-empty string.")
        if not isinstance(self.type_symbol, str) or not self.type_symbol:
            raise ValueError("AtomSite.type_symbol must be a non-empty string.")
        for field_name in ("fract_x", "fract_y", "fract_z"):
            object.__setattr__(
                self,
                field_name,
                _finite_float(getattr(self, field_name), f"AtomSite.{field_name}"),
            )
        if self.occupancy is not None:
            occupancy = _finite_float(self.occupancy, "AtomSite.occupancy")
            if occupancy < 0.0 or occupancy > 1.0:
                raise ValueError(f"AtomSite.occupancy must be between 0 and 1, got {occupancy!r}.")
            object.__setattr__(self, "occupancy", occupancy)

    @property
    def fractional_coordinates(self) -> tuple[float, float, float]:
        """Return ``(x, y, z)`` fractional direct-cell coordinates."""
        return (self.fract_x, self.fract_y, self.fract_z)


@dataclass(frozen=True)
class CrystalStructure:
    """A small imported crystal-structure record.

    Args:
        data_name: CIF data-block name without the ``data_`` prefix.
        cell: Validated unit cell.
        atom_sites: Atom sites in deterministic CIF order.
        space_group_symbol: Space-group symbol as read or normalized by import.
        space_group_number: Optional International Tables number.
        source_format: Provenance label for the imported source.
        parser_version: Stable parser version identifier.

    Raises:
        ValueError: If identifiers are empty or atom sites are malformed.
    """

    data_name: str
    cell: UnitCell
    atom_sites: tuple[AtomSite, ...]
    space_group_symbol: str
    space_group_number: int | None = None
    source_format: str = "cif"
    parser_version: str = "cif-v0"

    def __post_init__(self) -> None:
        if not isinstance(self.data_name, str) or not self.data_name:
            raise ValueError("CrystalStructure.data_name must be a non-empty string.")
        if not isinstance(self.cell, UnitCell):
            raise TypeError("CrystalStructure.cell must be a UnitCell.")
        atom_sites = tuple(self.atom_sites)
        if any(not isinstance(site, AtomSite) for site in atom_sites):
            raise TypeError("CrystalStructure.atom_sites must contain AtomSite records.")
        if not isinstance(self.space_group_symbol, str) or not self.space_group_symbol:
            raise ValueError("CrystalStructure.space_group_symbol must be a non-empty string.")
        if self.space_group_number is not None:
            if isinstance(self.space_group_number, bool) or not isinstance(self.space_group_number, int):
                raise ValueError("CrystalStructure.space_group_number must be an integer when provided.")
            if self.space_group_number < 1 or self.space_group_number > 230:
                raise ValueError("CrystalStructure.space_group_number must be between 1 and 230.")
        if not self.source_format:
            raise ValueError("CrystalStructure.source_format must be non-empty.")
        if not self.parser_version:
            raise ValueError("CrystalStructure.parser_version must be non-empty.")
        object.__setattr__(self, "atom_sites", atom_sites)


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)
