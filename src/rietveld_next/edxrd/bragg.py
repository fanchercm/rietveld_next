"""Fixed-angle Bragg conversions for energy-dispersive X-ray diffraction."""

from __future__ import annotations

import math

HC_KEV_ANGSTROM = 12.398419843320026
"""Planck constant times speed of light in keV angstrom."""


def fixed_angle_bragg_energy_keV(
    d_spacing_angstrom: float,
    two_theta_degrees: float,
    *,
    order: int = 1,
) -> float:
    """Convert d-spacing to EDXRD photon energy at fixed scattering angle.

    The conversion combines Bragg's law with ``E = hc / lambda``:

    ```text
    E_keV = order * hc_keV_angstrom / (2 d sin(two_theta / 2))
    ```

    Args:
        d_spacing_angstrom: Positive lattice-plane spacing in angstroms.
        two_theta_degrees: Fixed scattering angle in degrees two-theta. The
            supported range is ``0 < two_theta_degrees <= 180``.
        order: Positive diffraction order ``n``.

    Returns:
        Photon energy in keV.

    Raises:
        ValueError: If inputs are non-finite, non-positive, or outside the
            supported angle/order bounds.

    Example:
        >>> round(fixed_angle_bragg_energy_keV(1.0, 60.0), 6)
        12.39842
    """

    d_spacing = _positive_finite_float(d_spacing_angstrom, "d_spacing_angstrom")
    sine_theta = _bragg_sine_theta(two_theta_degrees)
    diffraction_order = _positive_order(order)
    return diffraction_order * HC_KEV_ANGSTROM / (2.0 * d_spacing * sine_theta)


def fixed_angle_bragg_d_spacing_angstrom(
    energy_keV: float,
    two_theta_degrees: float,
    *,
    order: int = 1,
) -> float:
    """Convert EDXRD photon energy to d-spacing at fixed scattering angle.

    The conversion combines Bragg's law with ``lambda = hc / E``:

    ```text
    d_angstrom = order * hc_keV_angstrom / (2 E_keV sin(two_theta / 2))
    ```

    Args:
        energy_keV: Positive photon energy in keV.
        two_theta_degrees: Fixed scattering angle in degrees two-theta. The
            supported range is ``0 < two_theta_degrees <= 180``.
        order: Positive diffraction order ``n``.

    Returns:
        Lattice-plane spacing in angstroms.

    Raises:
        ValueError: If inputs are non-finite, non-positive, or outside the
            supported angle/order bounds.

    Example:
        >>> energy = fixed_angle_bragg_energy_keV(1.0, 60.0)
        >>> round(fixed_angle_bragg_d_spacing_angstrom(energy, 60.0), 6)
        1.0
    """

    energy = _positive_finite_float(energy_keV, "energy_keV")
    sine_theta = _bragg_sine_theta(two_theta_degrees)
    diffraction_order = _positive_order(order)
    return diffraction_order * HC_KEV_ANGSTROM / (2.0 * energy * sine_theta)


def _bragg_sine_theta(two_theta_degrees: float) -> float:
    two_theta = _positive_finite_float(two_theta_degrees, "two_theta_degrees")
    if two_theta > 180.0:
        raise ValueError("two_theta_degrees must be less than or equal to 180 degrees.")
    return math.sin(math.radians(0.5 * two_theta))


def _positive_order(order: int) -> int:
    if isinstance(order, bool) or not isinstance(order, int) or order <= 0:
        raise ValueError(f"order must be a positive integer, got {order!r}.")
    return order


def _positive_finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    numeric_value = float(value)
    if numeric_value <= 0.0:
        raise ValueError(f"{name} must be positive, got {numeric_value!r}.")
    return numeric_value
