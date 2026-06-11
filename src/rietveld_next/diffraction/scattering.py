"""Reference scattering helpers for small diffraction-model increments.

The data and calculations here are intentionally dependency-free. The X-ray
form-factor table is a tiny neutral-atom Cromer-Mann subset for early API
plumbing and tests; it is not a complete production scattering table.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import itertools
import math


@dataclass(frozen=True)
class XRayFormFactorCoefficients:
    """Neutral-atom Cromer-Mann X-ray form-factor coefficients.

    The tabulated expression is:

    ```text
    f0(s) = sum_i a_i exp(-b_i s^2) + c
    s = sin(theta) / wavelength
    ```

    Args:
        symbol: Element symbol for the neutral atom.
        a: Four Cromer-Mann ``a`` coefficients.
        b: Four Cromer-Mann ``b`` coefficients in square angstroms.
        c: Constant Cromer-Mann coefficient.
        source: Human-readable provenance label.
        note: Scope note for table completeness and validation status.
    """

    symbol: str
    a: tuple[float, float, float, float]
    b: tuple[float, float, float, float]
    c: float
    source: str
    note: str


_CROMER_MANN_SOURCE = (
    "International Tables for Crystallography, Vol. C, Table 6.1.1.4 "
    "neutral-atom Cromer-Mann coefficients; rounded common tabulation."
)
_INCOMPLETE_TABLE_NOTE = (
    "Small startup subset only; use for deterministic plumbing tests, not "
    "complete production refinement coverage."
)
_XRAY_FORM_FACTORS: dict[str, XRayFormFactorCoefficients] = {
    "C": XRayFormFactorCoefficients(
        symbol="C",
        a=(2.3100, 1.0200, 1.5886, 0.8650),
        b=(20.8439, 10.2075, 0.5687, 51.6512),
        c=0.2156,
        source=_CROMER_MANN_SOURCE,
        note=_INCOMPLETE_TABLE_NOTE,
    ),
    "O": XRayFormFactorCoefficients(
        symbol="O",
        a=(3.0485, 2.2868, 1.5463, 0.8670),
        b=(13.2771, 5.7011, 0.3239, 32.9089),
        c=0.2508,
        source=_CROMER_MANN_SOURCE,
        note=_INCOMPLETE_TABLE_NOTE,
    ),
    "Si": XRayFormFactorCoefficients(
        symbol="Si",
        a=(6.2915, 3.0353, 1.9891, 1.5410),
        b=(2.4386, 32.3337, 0.6785, 81.6937),
        c=1.1407,
        source=_CROMER_MANN_SOURCE,
        note=_INCOMPLETE_TABLE_NOTE,
    ),
}


def available_xray_form_factor_symbols() -> tuple[str, ...]:
    """Return supported X-ray form-factor element symbols.

    Returns:
        Supported symbols sorted alphabetically for deterministic display.

    Example:
        >>> available_xray_form_factor_symbols()
        ('C', 'O', 'Si')
    """
    return tuple(sorted(_XRAY_FORM_FACTORS))


def lookup_xray_form_factor_coefficients(symbol: str) -> XRayFormFactorCoefficients:
    """Return Cromer-Mann coefficients for a supported element symbol.

    Args:
        symbol: Exact element symbol, currently ``"C"``, ``"O"``, or ``"Si"``.

    Returns:
        Coefficients and provenance metadata.

    Raises:
        ValueError: If ``symbol`` is not a non-empty string.
        KeyError: If ``symbol`` is not in the startup subset.

    Example:
        >>> lookup_xray_form_factor_coefficients("Si").c
        1.1407
    """
    if not isinstance(symbol, str) or not symbol:
        raise ValueError("symbol must be a non-empty string.")
    try:
        return _XRAY_FORM_FACTORS[symbol]
    except KeyError as exc:
        available = ", ".join(available_xray_form_factor_symbols())
        raise KeyError(f"Unsupported X-ray form-factor symbol {symbol!r}. Available symbols: {available}.") from exc


def evaluate_xray_form_factor(symbol: str, sin_theta_over_wavelength_inv_angstrom: float) -> float:
    """Evaluate a neutral-atom X-ray form factor from the startup subset.

    Args:
        symbol: Exact element symbol in the coefficient subset.
        sin_theta_over_wavelength_inv_angstrom: ``sin(theta) / wavelength`` in
            inverse angstroms. Must be finite and non-negative.

    Returns:
        Dimensionless electron scattering factor ``f0(s)``.

    Raises:
        ValueError: If ``sin_theta_over_wavelength_inv_angstrom`` is invalid.
        KeyError: If ``symbol`` is unsupported.

    Example:
        >>> round(evaluate_xray_form_factor("C", 0.0), 4)
        5.9992
    """
    coefficients = lookup_xray_form_factor_coefficients(symbol)
    scattering_vector = _finite_float(
        sin_theta_over_wavelength_inv_angstrom,
        "sin_theta_over_wavelength_inv_angstrom",
    )
    if scattering_vector < 0.0:
        raise ValueError(
            "sin_theta_over_wavelength_inv_angstrom must be non-negative, "
            f"got {scattering_vector!r}."
        )

    squared = scattering_vector * scattering_vector
    return sum(
        a_value * math.exp(-b_value * squared)
        for a_value, b_value in zip(coefficients.a, coefficients.b, strict=True)
    ) + coefficients.c


def equivalent_miller_indices_by_sign_permutation(hkl: Sequence[int]) -> tuple[tuple[int, int, int], ...]:
    """Return simple sign/permutation equivalents for a Miller index.

    This helper intentionally counts only permutations of ``|h|, |k|, |l|``
    and independent signs on non-zero entries. It is a deterministic reference
    utility, not a full space-group multiplicity engine.

    Args:
        hkl: Three integer Miller indices ``(h, k, l)``.

    Returns:
        Sorted unique equivalent Miller indices.

    Raises:
        ValueError: If ``hkl`` is not a three-item integer sequence.

    Example:
        >>> equivalent_miller_indices_by_sign_permutation((1, 1, 0))
        ((-1, -1, 0), (-1, 0, -1), (-1, 0, 1), (-1, 1, 0), (0, -1, -1), (0, -1, 1), (0, 1, -1), (0, 1, 1), (1, -1, 0), (1, 0, -1), (1, 0, 1), (1, 1, 0))
    """
    miller = _validate_miller_indices(hkl)
    absolute_values = tuple(abs(index) for index in miller)
    equivalents: set[tuple[int, int, int]] = set()
    for permutation in set(itertools.permutations(absolute_values, 3)):
        sign_options = tuple((-1, 1) if value != 0 else (1,) for value in permutation)
        for signs in itertools.product(*sign_options):
            equivalents.add(tuple(value * sign for value, sign in zip(permutation, signs, strict=True)))
    return tuple(sorted(equivalents))


def simple_miller_multiplicity(hkl: Sequence[int]) -> int:
    """Count simple sign/permutation Miller-index equivalents.

    Args:
        hkl: Three integer Miller indices ``(h, k, l)``.

    Returns:
        Number of unique sign/permutation equivalents.

    Raises:
        ValueError: If ``hkl`` is not a three-item integer sequence.

    Example:
        >>> simple_miller_multiplicity((1, 2, 3))
        48
    """
    return len(equivalent_miller_indices_by_sign_permutation(hkl))


def _validate_miller_indices(hkl: Sequence[int]) -> tuple[int, int, int]:
    if isinstance(hkl, str) or not isinstance(hkl, Sequence):
        raise ValueError("hkl must be a three-item sequence of integers.")
    if len(hkl) != 3:
        raise ValueError(f"hkl must contain exactly three indices, got {len(hkl)}.")
    indices: list[int] = []
    for axis_name, value in zip(("h", "k", "l"), hkl, strict=True):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{axis_name} must be an integer Miller index, got {value!r}.")
        indices.append(value)
    return indices[0], indices[1], indices[2]


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)
