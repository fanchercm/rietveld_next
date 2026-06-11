"""Small neutron bound coherent scattering-length lookup table.

The values included here are a deliberately small reference subset for early
lookup plumbing. They use femtometer units and are attributed to the NIST
Center for Neutron Research scattering length tables in the returned metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


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
    "C": NeutronScatteringLength("nat C", 6.6460, _SOURCE),
    "nat C": NeutronScatteringLength("nat C", 6.6460, _SOURCE),
    "O": NeutronScatteringLength("nat O", 5.803, _SOURCE),
    "nat O": NeutronScatteringLength("nat O", 5.803, _SOURCE),
}
_ISOTOPE_PREFIX = re.compile(r"^([0-9]+)([A-Za-z][A-Za-z]?)$")
_ISOTOPE_SUFFIX = re.compile(r"^([A-Za-z][A-Za-z]?)-([0-9]+)$")


def lookup_bound_coherent_scattering_length(isotope: str) -> NeutronScatteringLength:
    """Return a bound coherent neutron scattering length by isotope label.

    Args:
        isotope: Isotope key. Supported keys include natural-element labels
            such as ``"C"`` and ``"nat C"``, mass-prefixed isotope labels such
            as ``"1H"``, the isotope-suffix form ``"H-2"``, and ``"D"`` for
            deuterium.

    Returns:
        Scattering length metadata with value in femtometers.

    Raises:
        ValueError: If ``isotope`` is not a non-empty string.
        KeyError: If the isotope is not present in the current table subset.

    Example:
        >>> lookup_bound_coherent_scattering_length("H-2").bound_coherent_fm
        6.671
    """
    key = normalize_neutron_isotope_label(isotope)
    try:
        return _BOUND_COHERENT_FM[key]
    except KeyError as exc:
        available = ", ".join(available_bound_coherent_scattering_lengths())
        raise KeyError(f"Unsupported neutron isotope {isotope!r}. Available keys: {available}.") from exc


def normalize_neutron_isotope_label(isotope: str) -> str:
    """Normalize supported neutron isotope labels to lookup-table keys.

    Args:
        isotope: User-facing isotope label. Leading and trailing whitespace is
            ignored. The natural-label prefix ``nat`` is normalized to
            ``"nat X"`` and suffix labels such as ``"H-2"`` are normalized to
            ``"2H"``.

    Returns:
        Canonical lookup key for the current table subset.

    Raises:
        ValueError: If ``isotope`` is not a non-empty string.

    Example:
        >>> normalize_neutron_isotope_label(" H-2 ")
        '2H'
    """
    if not isinstance(isotope, str) or not isotope.strip():
        raise ValueError("isotope must be a non-empty string.")
    label = " ".join(isotope.strip().split())
    if label.lower().startswith("nat "):
        parts = label.split(" ", maxsplit=1)
        return f"nat {_normalize_element_symbol(parts[1])}"
    if label.upper() == "D":
        return "D"
    prefix_match = _ISOTOPE_PREFIX.match(label)
    if prefix_match:
        mass_number, symbol = prefix_match.groups()
        return f"{mass_number}{_normalize_element_symbol(symbol)}"
    suffix_match = _ISOTOPE_SUFFIX.match(label)
    if suffix_match:
        symbol, mass_number = suffix_match.groups()
        return f"{mass_number}{_normalize_element_symbol(symbol)}"
    return _normalize_element_symbol(label)


def available_bound_coherent_scattering_lengths() -> tuple[str, ...]:
    """Return supported bound coherent scattering-length lookup keys.

    Returns:
        Deterministically sorted isotope labels for the current small table.

    Example:
        >>> "2H" in available_bound_coherent_scattering_lengths()
        True
    """

    return tuple(sorted(_BOUND_COHERENT_FM))


def _normalize_element_symbol(symbol: str) -> str:
    if not symbol.isalpha() or len(symbol) > 2:
        return symbol
    return symbol[0].upper() + symbol[1:].lower()
