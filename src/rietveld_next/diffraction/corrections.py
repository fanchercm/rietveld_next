"""Small diffraction correction helpers with explicit validation."""

from __future__ import annotations

import math


def lorentz_polarization_correction(
    two_theta_degrees: float,
    *,
    polarization_fraction: float = 0.5,
) -> float:
    """Return a continuous-wave powder Lorentz-polarization correction.

    The implemented reference expression is:

    ```text
    theta = two_theta / 2
    P = (1 - K) + K cos(2 theta)^2
    LP = P / (sin(theta)^2 cos(theta))
    ```

    where ``K`` is ``polarization_fraction`` on ``[0, 1]``. ``K=0.5`` gives
    the common unpolarized factor ``(1 + cos(2 theta)^2) / 2``.

    Args:
        two_theta_degrees: Scattering angle in degrees two-theta. Must be
            finite and strictly between 0 and 180 degrees.
        polarization_fraction: Linear polarization blend ``K`` on ``[0, 1]``.

    Returns:
        Multiplicative Lorentz-polarization correction factor.

    Raises:
        ValueError: If the angle is outside ``(0, 180)`` degrees, the
            polarization fraction is outside ``[0, 1]``, or any input is
            non-finite.

    Example:
        >>> round(lorentz_polarization_correction(90.0), 6)
        1.414214
    """
    two_theta = _finite_float(two_theta_degrees, "two_theta_degrees")
    polarization = _finite_float(polarization_fraction, "polarization_fraction")
    if not 0.0 < two_theta < 180.0:
        raise ValueError(f"two_theta_degrees must be between 0 and 180 degrees, got {two_theta!r}.")
    if not 0.0 <= polarization <= 1.0:
        raise ValueError(f"polarization_fraction must be between 0 and 1, got {polarization!r}.")

    theta_radians = math.radians(0.5 * two_theta)
    cos_two_theta = math.cos(2.0 * theta_radians)
    polarization_factor = (1.0 - polarization) + polarization * cos_two_theta * cos_two_theta
    lorentz_denominator = math.sin(theta_radians) ** 2 * math.cos(theta_radians)
    return polarization_factor / lorentz_denominator


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)
