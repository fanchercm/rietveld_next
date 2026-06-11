"""Wavelength validation and simple continuous-wave X-ray helpers."""

from __future__ import annotations

import math


def validate_wavelength_angstrom(wavelength_angstrom: float) -> float:
    """Validate a positive finite X-ray wavelength in angstroms.

    Args:
        wavelength_angstrom: Incident radiation wavelength in angstroms.

    Returns:
        The wavelength as a ``float``.

    Raises:
        ValueError: If the wavelength is not finite and strictly positive.

    Example:
        >>> validate_wavelength_angstrom(1.5406)
        1.5406
    """
    wavelength = _finite_float(wavelength_angstrom, "wavelength_angstrom")
    if wavelength <= 0.0:
        raise ValueError(f"wavelength_angstrom must be positive, got {wavelength!r}.")
    return wavelength


def bragg_two_theta_degrees(d_spacing_angstrom: float, wavelength_angstrom: float, *, order: int = 1) -> float:
    """Compute a Bragg peak position for continuous-wave diffraction.

    This helper implements Bragg's law for a single reflection:

    ```text
    n lambda = 2 d sin(theta)
    two_theta = 2 theta
    ```

    Args:
        d_spacing_angstrom: Lattice-plane spacing in angstroms. Must be
            positive.
        wavelength_angstrom: Incident wavelength in angstroms. Must be
            positive.
        order: Positive diffraction order ``n``.

    Returns:
        Peak position in degrees two-theta.

    Raises:
        ValueError: If inputs are invalid or the requested reflection is not
            physically reachable because ``n * wavelength > 2 * d``.

    Example:
        >>> round(bragg_two_theta_degrees(1.0, 1.0), 6)
        60.0
    """
    d_spacing = _finite_float(d_spacing_angstrom, "d_spacing_angstrom")
    wavelength = validate_wavelength_angstrom(wavelength_angstrom)
    if d_spacing <= 0.0:
        raise ValueError(f"d_spacing_angstrom must be positive, got {d_spacing!r}.")
    if isinstance(order, bool) or not isinstance(order, int) or order <= 0:
        raise ValueError(f"order must be a positive integer, got {order!r}.")

    argument = order * wavelength / (2.0 * d_spacing)
    if argument > 1.0:
        raise ValueError(
            "Bragg condition is unreachable: order * wavelength_angstrom "
            "must be less than or equal to 2 * d_spacing_angstrom."
        )
    return math.degrees(2.0 * math.asin(argument))


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)
