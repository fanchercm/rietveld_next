"""Residual vector kernels for refinement objectives."""

from __future__ import annotations

import math
from collections.abc import Sequence


def residual_vector(
    observed: Sequence[float],
    calculated: Sequence[float],
    sigma: Sequence[float] | None = None,
) -> list[float]:
    """Compute an unweighted or uncertainty-weighted residual vector.

    The residual convention is:

    ```text
    r_i = observed_i - calculated_i
    ```

    When ``sigma`` is supplied, the weighted residual convention is:

    ```text
    r_i = (observed_i - calculated_i) / sigma_i
    ```

    All inputs are unit-compatible intensity values. ``sigma`` values represent
    one-standard-deviation uncertainty in the same intensity units and must be
    strictly positive.

    Args:
        observed: Observed intensities.
        calculated: Calculated intensities.
        sigma: Optional positive standard uncertainties.

    Returns:
        Residual values in deterministic input order.

    Raises:
        ValueError: If inputs are not finite numeric sequences, lengths differ,
            or any supplied uncertainty is non-positive.

    Example:
        >>> residual_vector([10.0, 12.0], [9.0, 13.0])
        [1.0, -1.0]
    """
    observed_values = _finite_sequence(observed, "observed")
    calculated_values = _finite_sequence(calculated, "calculated")
    if len(observed_values) != len(calculated_values):
        raise ValueError(
            "observed and calculated must have the same length, "
            f"got {len(observed_values)} and {len(calculated_values)}."
        )

    raw = [obs - calc for obs, calc in zip(observed_values, calculated_values, strict=True)]
    if sigma is None:
        return raw

    sigma_values = _finite_sequence(sigma, "sigma")
    if len(sigma_values) != len(observed_values):
        raise ValueError(
            "sigma must have the same length as observed, "
            f"got {len(sigma_values)} and {len(observed_values)}."
        )
    for index, sigma_value in enumerate(sigma_values):
        if sigma_value <= 0.0:
            raise ValueError(f"sigma[{index}] must be positive, got {sigma_value!r}.")
    return [value / sigma_value for value, sigma_value in zip(raw, sigma_values, strict=True)]


def _finite_sequence(values: Sequence[float], name: str) -> list[float]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    return [_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values)]


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)

