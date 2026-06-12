"""Minimal CIF import and validation reporting.

This parser intentionally supports a small CIF v0 subset for deterministic
startup tests. It handles scalar cell/space-group tags and simple atom-site
loops, but it is not a full STAR/CIF parser.
"""

from __future__ import annotations

from dataclasses import dataclass
import shlex
from typing import Any

from rietveld_next.structure.models import AtomSite, CrystalStructure, UnitCell
from rietveld_next.structure.symmetry import lookup_space_group


@dataclass(frozen=True)
class CifValidationIssue:
    """Single CIF validation report issue."""

    code: str
    field: str
    message: str
    severity: str = "error"

    def __post_init__(self) -> None:
        """Validate report issue fields."""
        for name, value in (("code", self.code), ("field", self.field), ("message", self.message)):
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} must be a non-empty string.")
        if self.severity not in {"error", "warning"}:
            raise ValueError("severity must be 'error' or 'warning'.")

    def to_dict(self) -> dict[str, str]:
        """Return a deterministic JSON-compatible issue mapping."""
        return {
            "code": self.code,
            "field": self.field,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class CifValidationReport:
    """Validation report for minimal CIF import."""

    issues: tuple[CifValidationIssue, ...]

    @property
    def ok(self) -> bool:
        """Return whether no error-severity issues are present."""
        return all(issue.severity != "error" for issue in self.issues)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible report mapping."""
        return {"issues": [issue.to_dict() for issue in self.issues], "ok": self.ok}


def validate_cif_text(cif_text: str) -> CifValidationReport:
    """Validate the small CIF subset supported by ``import_cif_v0``.

    Args:
        cif_text: CIF text to validate.

    Returns:
        Deterministic validation report.
    """
    scalars, atom_rows = _parse_cif_subset(cif_text)
    issues: list[CifValidationIssue] = []
    for field in (
        "_cell_length_a",
        "_cell_length_b",
        "_cell_length_c",
        "_cell_angle_alpha",
        "_cell_angle_beta",
        "_cell_angle_gamma",
    ):
        if field not in scalars:
            issues.append(CifValidationIssue("missing_field", field, f"Required CIF field {field} is missing."))
            continue
        try:
            _parse_cif_number(scalars[field])
        except ValueError as exc:
            issues.append(CifValidationIssue("invalid_number", field, str(exc)))
    if _space_group_symbol(scalars) is None:
        issues.append(
            CifValidationIssue(
                "missing_space_group",
                "_space_group_name_H-M_alt",
                "CIF is missing a supported space-group symbol field.",
            )
        )
    if not atom_rows:
        issues.append(CifValidationIssue("missing_atom_sites", "_atom_site", "CIF contains no atom-site loop rows."))
    else:
        for index, row in enumerate(atom_rows):
            for field in ("_atom_site_label", "_atom_site_fract_x", "_atom_site_fract_y", "_atom_site_fract_z"):
                if field not in row:
                    issues.append(CifValidationIssue("missing_atom_site_field", field, f"Atom row {index} omits {field}."))
            for field in ("_atom_site_fract_x", "_atom_site_fract_y", "_atom_site_fract_z", "_atom_site_occupancy"):
                if field in row:
                    try:
                        _parse_cif_number(row[field])
                    except ValueError as exc:
                        issues.append(CifValidationIssue("invalid_atom_number", field, str(exc)))
    return CifValidationReport(tuple(issues))


def import_cif_v0(cif_text: str) -> CrystalStructure:
    """Import a representative simple CIF into a typed structure record.

    Args:
        cif_text: CIF text containing cell metadata, a supported space-group
            symbol, and a simple atom-site loop.

    Returns:
        Imported crystal structure.

    Raises:
        ValueError: If validation fails or the space group is unsupported.
    """
    report = validate_cif_text(cif_text)
    if not report.ok:
        first = report.issues[0]
        raise ValueError(f"{first.code} at {first.field}: {first.message}")
    scalars, atom_rows = _parse_cif_subset(cif_text)
    symbol = _space_group_symbol(scalars)
    if symbol is None:
        raise ValueError("missing_space_group")
    space_group = lookup_space_group(symbol)
    atom_sites = tuple(
        AtomSite(
            label=row["_atom_site_label"],
            type_symbol=row.get("_atom_site_type_symbol", row["_atom_site_label"]),
            fract_x=_parse_cif_number(row["_atom_site_fract_x"]),
            fract_y=_parse_cif_number(row["_atom_site_fract_y"]),
            fract_z=_parse_cif_number(row["_atom_site_fract_z"]),
            occupancy=_parse_cif_number(row["_atom_site_occupancy"]) if "_atom_site_occupancy" in row else None,
        )
        for row in atom_rows
    )
    return CrystalStructure(
        data_name=scalars.get("data_", "imported"),
        cell=UnitCell(
            _parse_cif_number(scalars["_cell_length_a"]),
            _parse_cif_number(scalars["_cell_length_b"]),
            _parse_cif_number(scalars["_cell_length_c"]),
            _parse_cif_number(scalars["_cell_angle_alpha"]),
            _parse_cif_number(scalars["_cell_angle_beta"]),
            _parse_cif_number(scalars["_cell_angle_gamma"]),
        ),
        atom_sites=atom_sites,
        space_group_symbol=space_group.hermann_mauguin,
        space_group_number=space_group.number,
    )


def _parse_cif_subset(cif_text: str) -> tuple[dict[str, str], list[dict[str, str]]]:
    if not isinstance(cif_text, str) or not cif_text.strip():
        raise ValueError("cif_text must be a non-empty string.")
    lines = _logical_lines(cif_text)
    scalars: dict[str, str] = {}
    atom_rows: list[dict[str, str]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.casefold().startswith("data_"):
            scalars["data_"] = line[5:] or "imported"
            index += 1
            continue
        if line == "loop_":
            index += 1
            headers: list[str] = []
            while index < len(lines) and lines[index].startswith("_"):
                headers.append(lines[index].split()[0])
                index += 1
            rows: list[list[str]] = []
            while index < len(lines) and not lines[index].startswith("_") and lines[index] != "loop_":
                tokens = shlex.split(lines[index])
                if tokens:
                    rows.append(tokens)
                index += 1
            if any(header.startswith("_atom_site_") for header in headers):
                for row in rows:
                    if len(row) >= len(headers):
                        atom_rows.append(dict(zip(headers, row, strict=False)))
            continue
        if line.startswith("_"):
            tokens = shlex.split(line)
            if len(tokens) >= 2:
                scalars[tokens[0]] = tokens[1]
        index += 1
    return scalars, atom_rows


def _logical_lines(cif_text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in cif_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def _space_group_symbol(scalars: dict[str, str]) -> str | None:
    for field in (
        "_space_group_name_H-M_alt",
        "_symmetry_space_group_name_H-M",
        "_space_group_IT_number",
    ):
        if field in scalars:
            return scalars[field]
    return None


def _parse_cif_number(value: str) -> float:
    token = str(value).strip().strip("'\"")
    if "(" in token and token.endswith(")"):
        token = token[: token.index("(")]
    try:
        return float(token)
    except ValueError as exc:
        raise ValueError(f"CIF numeric value {value!r} is not supported by the v0 parser.") from exc
