"""Magnetic neutron form-factor lookup helpers.

The startup table is a small ``<j0>`` coefficient subset for magnetic neutron
scattering API plumbing. It is provenance-labeled and intentionally incomplete;
unsupported ions fail explicitly rather than falling back to unverified values.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Any


@dataclass(frozen=True)
class MagneticFormFactorCoefficients:
    """Analytical ``<j0>`` magnetic form-factor coefficients for one ion.

    The tabulated expression is:

    ```text
    <j0(Q)> = sum_i a_i exp(-b_i * (Q / 4*pi)^2) + c
    ```

    Args:
        ion: Canonical ion label, such as ``"Fe2+"``.
        angular_momentum: Spherical Bessel expectation represented by this
            coefficient set. The startup subset currently supports ``"j0"``.
        a: Three dimensionless exponential amplitudes.
        b_square_angstrom: Three exponential coefficients in square angstroms.
        c: Dimensionless constant term.
        source: Human-readable provenance label.
        note: Scope note for table completeness and validation status.
    """

    ion: str
    angular_momentum: str
    a: tuple[float, float, float]
    b_square_angstrom: tuple[float, float, float]
    c: float
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible representation.

        Returns:
            Mapping with coefficients, units, expression, and provenance.

        Example:
            >>> lookup_magnetic_form_factor_coefficients("Fe2+").to_dict()["ion"]
            'Fe2+'
        """

        return {
            "ion": self.ion,
            "angular_momentum": self.angular_momentum,
            "a": list(self.a),
            "b_square_angstrom": list(self.b_square_angstrom),
            "c": self.c,
            "q_units": "inverse_angstrom",
            "expression": "<j0(Q)> = sum_i a_i exp(-b_i * (Q / 4*pi)^2) + c",
            "source": self.source,
            "note": self.note,
        }


_BROWN_SOURCE = (
    "P. J. Brown, International Tables for Crystallography Vol. C, section 4.4.5; "
    "3d-ion <j0> coefficients as mirrored by McPhase and PeriodicTable."
)
_INCOMPLETE_TABLE_NOTE = (
    "Small startup subset only; use for deterministic plumbing tests, not "
    "complete production magnetic refinement coverage."
)
_MAGNETIC_FORM_FACTORS: dict[str, MagneticFormFactorCoefficients] = {
    "Mn2+": MagneticFormFactorCoefficients(
        ion="Mn2+",
        angular_momentum="j0",
        a=(0.4220, 0.5948, 0.0043),
        b_square_angstrom=(17.6840, 6.0050, -0.6090),
        c=-0.0219,
        source=_BROWN_SOURCE,
        note=_INCOMPLETE_TABLE_NOTE,
    ),
    "Fe2+": MagneticFormFactorCoefficients(
        ion="Fe2+",
        angular_momentum="j0",
        a=(0.0263, 0.3668, 0.6188),
        b_square_angstrom=(34.9597, 15.9435, 5.5935),
        c=-0.0119,
        source=_BROWN_SOURCE,
        note=_INCOMPLETE_TABLE_NOTE,
    ),
    "Ni2+": MagneticFormFactorCoefficients(
        ion="Ni2+",
        angular_momentum="j0",
        a=(0.0163, 0.3916, 0.6052),
        b_square_angstrom=(35.8826, 13.2233, 4.3388),
        c=-0.0133,
        source=_BROWN_SOURCE,
        note=_INCOMPLETE_TABLE_NOTE,
    ),
}
_ION_LABEL = re.compile(r"^([A-Za-z][A-Za-z]?)([0-9]+)\+?$")
_ION_LABEL_PLUS_PREFIX = re.compile(r"^([A-Za-z][A-Za-z]?)\+([0-9]+)$")


def available_magnetic_form_factor_ions() -> tuple[str, ...]:
    """Return supported magnetic form-factor ion labels.

    Returns:
        Canonical ion labels sorted alphabetically for deterministic display.

    Example:
        >>> available_magnetic_form_factor_ions()
        ('Fe2+', 'Mn2+', 'Ni2+')
    """

    return tuple(sorted(_MAGNETIC_FORM_FACTORS))


def lookup_magnetic_form_factor_coefficients(ion: str) -> MagneticFormFactorCoefficients:
    """Return magnetic ``<j0>`` form-factor coefficients for a supported ion.

    Args:
        ion: Ion label. Supported labels include ``"Mn2+"``, ``"Fe2+"``, and
            ``"Ni2+"``. Whitespace is ignored and ``"Fe2"``/``"Fe+2"`` normalize
            to ``"Fe2+"``.

    Returns:
        Coefficients and provenance metadata for the canonical ion.

    Raises:
        ValueError: If ``ion`` is not a non-empty string.
        KeyError: If ``ion`` is not in the startup subset.

    Example:
        >>> lookup_magnetic_form_factor_coefficients("fe2").ion
        'Fe2+'
    """

    key = normalize_magnetic_ion_label(ion)
    try:
        return _MAGNETIC_FORM_FACTORS[key]
    except KeyError as exc:
        available = ", ".join(available_magnetic_form_factor_ions())
        raise KeyError(
            f"Unsupported magnetic form-factor ion {ion!r}. Available ions: {available}."
        ) from exc


def evaluate_magnetic_form_factor(
    ion: str,
    scattering_vector_inv_angstrom: float,
) -> float:
    """Evaluate the startup magnetic ``<j0>`` form factor at ``|Q|``.

    Args:
        ion: Supported magnetic ion label.
        scattering_vector_inv_angstrom: Magnitude of the scattering vector
            ``|Q|`` in inverse angstroms. Must be finite and non-negative.

    Returns:
        Dimensionless magnetic ``<j0(Q)>`` form factor from the rounded startup
        coefficient subset.

    Raises:
        ValueError: If ``scattering_vector_inv_angstrom`` is invalid.
        KeyError: If ``ion`` is unsupported.

    Example:
        >>> round(evaluate_magnetic_form_factor("Fe2+", 0.0), 4)
        1.0
    """

    coefficients = lookup_magnetic_form_factor_coefficients(ion)
    q_value = _non_negative_finite_float(
        scattering_vector_inv_angstrom,
        "scattering_vector_inv_angstrom",
    )
    reduced_q_squared = (q_value / (4.0 * math.pi)) ** 2
    return sum(
        amplitude * math.exp(-decay * reduced_q_squared)
        for amplitude, decay in zip(
            coefficients.a,
            coefficients.b_square_angstrom,
            strict=True,
        )
    ) + coefficients.c


def normalize_magnetic_ion_label(ion: str) -> str:
    """Normalize supported magnetic-ion labels to canonical lookup keys.

    Args:
        ion: User-facing ion label. Leading/trailing whitespace and internal
            whitespace are ignored. Examples include ``"fe2+"``, ``"Fe2"``,
            and ``"Fe+2"``.

    Returns:
        Canonical lookup key such as ``"Fe2+"``.

    Raises:
        ValueError: If ``ion`` is not a non-empty string or cannot be parsed as
            an element symbol plus integer positive charge.

    Example:
        >>> normalize_magnetic_ion_label(" fe+2 ")
        'Fe2+'
    """

    if not isinstance(ion, str) or not ion.strip():
        raise ValueError("ion must be a non-empty string.")
    label = "".join(ion.strip().split())
    match = _ION_LABEL.match(label) or _ION_LABEL_PLUS_PREFIX.match(label)
    if match is None:
        raise ValueError(
            "ion must be an element symbol followed by an integer positive charge, "
            "for example 'Fe2+'."
        )
    symbol, charge_text = match.groups()
    charge = int(charge_text)
    if charge <= 0:
        raise ValueError("ion charge must be positive.")
    return f"{_normalize_element_symbol(symbol)}{charge}+"


def _normalize_element_symbol(symbol: str) -> str:
    return symbol[0].upper() + symbol[1:].lower()


def _non_negative_finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number.")
    number = float(value)
    if number < 0.0:
        raise ValueError(f"{name} must be non-negative.")
    return number
