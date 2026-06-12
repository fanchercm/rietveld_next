"""Small space-group metadata lookup service.

This module is a deliberately tiny registry for early structural IO plumbing.
It is not a replacement for a crystallographic symmetry engine.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SpaceGroupInfo:
    """Metadata for a supported space group.

    Args:
        number: International Tables number.
        hermann_mauguin: Conventional Hermann-Mauguin symbol.
        crystal_system: Crystal system name.
        lattice_centering: One-letter lattice centering code.
        supported_operations: Whether this release implements symmetry
            operations for reflection generation.
        aliases: Accepted lookup aliases.
        note: Scope note describing registry limitations.
    """

    number: int
    hermann_mauguin: str
    crystal_system: str
    lattice_centering: str
    supported_operations: bool
    aliases: tuple[str, ...]
    note: str

    def __post_init__(self) -> None:
        if self.number < 1 or self.number > 230:
            raise ValueError("SpaceGroupInfo.number must be between 1 and 230.")
        for field_name in ("hermann_mauguin", "crystal_system", "lattice_centering", "note"):
            if not getattr(self, field_name):
                raise ValueError(f"SpaceGroupInfo.{field_name} must be non-empty.")
        aliases = tuple(self.aliases)
        if not aliases:
            raise ValueError("SpaceGroupInfo.aliases must not be empty.")
        object.__setattr__(self, "aliases", aliases)


_REGISTRY_NOTE = (
    "M12 startup metadata only; P1 has enough support for deterministic "
    "reflection enumeration, while other entries are lookup metadata only."
)
_SPACE_GROUPS: tuple[SpaceGroupInfo, ...] = (
    SpaceGroupInfo(
        number=1,
        hermann_mauguin="P 1",
        crystal_system="triclinic",
        lattice_centering="P",
        supported_operations=True,
        aliases=("P1", "P 1", "1"),
        note=_REGISTRY_NOTE,
    ),
    SpaceGroupInfo(
        number=227,
        hermann_mauguin="F d -3 m",
        crystal_system="cubic",
        lattice_centering="F",
        supported_operations=False,
        aliases=("Fd-3m", "F d -3 m", "F d -3 m :1", "227"),
        note=_REGISTRY_NOTE,
    ),
)


def available_space_groups() -> tuple[SpaceGroupInfo, ...]:
    """Return the supported startup space-group metadata in number order.

    Example:
        >>> [space_group.number for space_group in available_space_groups()]
        [1, 227]
    """
    return tuple(sorted(_SPACE_GROUPS, key=lambda space_group: space_group.number))


def lookup_space_group(identifier: str | int) -> SpaceGroupInfo:
    """Look up startup metadata by number or supported symbol alias.

    Args:
        identifier: International Tables number or a known textual alias such
            as ``"P 1"``, ``"P1"``, or ``"Fd-3m"``.

    Returns:
        Matching space-group metadata.

    Raises:
        ValueError: If ``identifier`` has the wrong type or is empty.
        KeyError: If the identifier is not in the startup registry.

    Example:
        >>> lookup_space_group("P1").number
        1
    """
    if isinstance(identifier, bool):
        raise ValueError("space-group identifier must be a string or integer.")
    if isinstance(identifier, int):
        try:
            return _SPACE_GROUPS_BY_NUMBER[identifier]
        except KeyError as exc:
            raise KeyError(f"Unsupported space-group number {identifier!r}.") from exc
    if not isinstance(identifier, str) or not identifier.strip():
        raise ValueError("space-group identifier must be a non-empty string or integer.")

    normalized_key = _normalize_space_group_key(identifier)
    try:
        return _SPACE_GROUPS_BY_ALIAS[normalized_key]
    except KeyError as exc:
        supported = ", ".join(space_group.hermann_mauguin for space_group in available_space_groups())
        raise KeyError(f"Unsupported space-group identifier {identifier!r}. Supported groups: {supported}.") from exc


def normalize_space_group_symbol(identifier: str | int) -> str:
    """Return the conventional symbol for a supported identifier."""
    return lookup_space_group(identifier).hermann_mauguin


def _normalize_space_group_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


_SPACE_GROUPS_BY_NUMBER = {space_group.number: space_group for space_group in _SPACE_GROUPS}
_SPACE_GROUPS_BY_ALIAS = {
    _normalize_space_group_key(alias): space_group
    for space_group in _SPACE_GROUPS
    for alias in (space_group.hermann_mauguin, *space_group.aliases)
}
