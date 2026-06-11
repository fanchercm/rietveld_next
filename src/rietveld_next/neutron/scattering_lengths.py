"""Small neutron bound coherent scattering-length lookup table.

The values included here are a deliberately small reference subset for early
lookup plumbing. They use femtometer units and are attributed to the NIST
Center for Neutron Research scattering length tables in the returned metadata.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NeutronScatteringLength:
    """Bound coherent neutron scattering length metadata.

    Args:
        isotope: Isotope label, such as ``"1H"`` or ``"nat C"``.
        bound_coherent_fm: Bound coherent scattering length in femtometers.
        source: Source label for provenance.
    """

    isotope: str
    bound_coherent_fm: float
    source: str


_SOURCE = "NIST Center for Neutron Research bound coherent scattering length tables"
_BOUND_COHERENT_FM: dict[str, NeutronScatteringLength] = {
    "H": NeutronScatteringLength("H", -3.7390, _SOURCE),
    "nat H": NeutronScatteringLength("H", -3.7390, _SOURCE),
    "1H": NeutronScatteringLength("1H", -3.7406, _SOURCE),
    "2H": NeutronScatteringLength("2H", 6.671, _SOURCE),
    "D": NeutronScatteringLength("2H", 6.671, _SOURCE),
    "nat C": NeutronScatteringLength("nat C", 6.6460, _SOURCE),
    "nat O": NeutronScatteringLength("nat O", 5.803, _SOURCE),
}


def lookup_bound_coherent_scattering_length(isotope: str) -> NeutronScatteringLength:
    """Return a bound coherent neutron scattering length by isotope label.

    Args:
        isotope: Exact isotope key. Supported keys are ``"H"``, ``"nat H"``,
            ``"1H"``, ``"2H"``, ``"D"``, ``"nat C"``, and ``"nat O"``.

    Returns:
        Scattering length metadata with value in femtometers.

    Raises:
        ValueError: If ``isotope`` is not a non-empty string.
        KeyError: If the isotope is not present in the current table subset.

    Example:
        >>> lookup_bound_coherent_scattering_length("1H").bound_coherent_fm
        -3.7406
    """
    if not isinstance(isotope, str) or not isotope:
        raise ValueError("isotope must be a non-empty string.")
    try:
        return _BOUND_COHERENT_FM[isotope]
    except KeyError as exc:
        available = ", ".join(sorted(_BOUND_COHERENT_FM))
        raise KeyError(f"Unsupported neutron isotope {isotope!r}. Available keys: {available}.") from exc
