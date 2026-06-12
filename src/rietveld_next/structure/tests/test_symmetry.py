"""Tests for startup structural metadata helpers."""

from __future__ import annotations

import math
import unittest

from rietveld_next.structure import (
    AtomSite,
    CrystalStructure,
    UnitCell,
    available_space_groups,
    generate_reflections,
    import_cif_v0,
    lookup_space_group,
    normalize_space_group_symbol,
    validate_cif_text,
)


class SpaceGroupLookupTests(unittest.TestCase):
    """Validate deterministic startup space-group lookup behavior."""

    def test_available_space_groups_are_number_sorted(self) -> None:
        numbers = [space_group.number for space_group in available_space_groups()]

        self.assertEqual(numbers, [1, 227])

    def test_lookup_accepts_number_and_symbol_aliases(self) -> None:
        self.assertEqual(lookup_space_group(1).hermann_mauguin, "P 1")
        self.assertEqual(lookup_space_group("P1").number, 1)
        self.assertEqual(lookup_space_group("F d -3 m :1").number, 227)
        self.assertEqual(normalize_space_group_symbol("fd-3m"), "F d -3 m")

    def test_lookup_reports_unsupported_identifier(self) -> None:
        with self.assertRaisesRegex(KeyError, "Unsupported space-group"):
            lookup_space_group("P 21/c")

    def test_lookup_rejects_bad_identifier_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "space-group identifier"):
            lookup_space_group(True)


class StructuralRecordTests(unittest.TestCase):
    """Validate typed structural records used by CIF and symmetry plumbing."""

    def test_unit_cell_volume_and_structure_record(self) -> None:
        cell = UnitCell(5.0, 5.0, 5.0, 90.0, 90.0, 90.0)
        site = AtomSite("Si1", "Si", 0.0, 0.0, 0.0, occupancy=1.0)
        structure = CrystalStructure(
            "silicon",
            cell,
            (site,),
            space_group_symbol=normalize_space_group_symbol("Fd-3m"),
            space_group_number=227,
        )

        self.assertAlmostEqual(structure.cell.volume_angstrom3, 125.0)
        self.assertEqual(structure.atom_sites[0].fractional_coordinates, (0.0, 0.0, 0.0))
        self.assertEqual(structure.space_group_symbol, "F d -3 m")

    def test_unit_cell_rejects_invalid_geometry(self) -> None:
        with self.assertRaisesRegex(ValueError, "UnitCell.a"):
            UnitCell(0.0, 1.0, 1.0, 90.0, 90.0, 90.0)
        with self.assertRaisesRegex(ValueError, "UnitCell.gamma"):
            UnitCell(1.0, 1.0, 1.0, 90.0, 90.0, math.inf)

    def test_atom_site_rejects_invalid_occupancy(self) -> None:
        with self.assertRaisesRegex(ValueError, "AtomSite.occupancy"):
            AtomSite("O1", "O", 0.0, 0.0, 0.0, occupancy=1.2)


class CifImportTests(unittest.TestCase):
    """Validate representative CIF import and reporting."""

    def test_import_simple_p1_cif(self) -> None:
        structure = import_cif_v0(_simple_p1_cif())

        self.assertEqual(structure.data_name, "nacl")
        self.assertEqual(structure.space_group_symbol, "P 1")
        self.assertEqual(len(structure.atom_sites), 2)
        self.assertEqual(structure.atom_sites[1].fractional_coordinates, (0.5, 0.5, 0.5))

    def test_validation_report_identifies_missing_fields(self) -> None:
        report = validate_cif_text("data_bad\n_cell_length_a 5.0\n")

        self.assertFalse(report.ok)
        codes = [issue.code for issue in report.issues]
        self.assertIn("missing_field", codes)
        self.assertIn("missing_space_group", codes)
        self.assertIn("missing_atom_sites", codes)

    def test_import_rejects_unsupported_numeric_value(self) -> None:
        report = validate_cif_text(_simple_p1_cif().replace("_cell_length_a 5.0", "_cell_length_a ?"))

        self.assertFalse(report.ok)
        self.assertIn("invalid_number", [issue.code for issue in report.issues])


class ReflectionGenerationTests(unittest.TestCase):
    """Validate deterministic P1 reflection generation."""

    def test_generate_p1_reflections_for_cubic_cell(self) -> None:
        reflections = generate_reflections(UnitCell(2.0, 2.0, 2.0, 90.0, 90.0, 90.0), "P1", max_index=1)

        self.assertEqual(len(reflections), 26)
        first_family = [reflection for reflection in reflections if abs(reflection.d_spacing_angstrom - 2.0) < 1.0e-12]
        self.assertEqual([(item.h, item.k, item.l) for item in first_family], [(-1, 0, 0), (0, -1, 0), (0, 0, -1), (0, 0, 1), (0, 1, 0), (1, 0, 0)])

    def test_generate_reflections_rejects_metadata_only_space_group(self) -> None:
        with self.assertRaisesRegex(ValueError, "not implemented"):
            generate_reflections(UnitCell(5.0, 5.0, 5.0, 90.0, 90.0, 90.0), "Fd-3m", max_index=1)


def _simple_p1_cif() -> str:
    return """
data_nacl
_cell_length_a 5.0
_cell_length_b 5.0
_cell_length_c 5.0
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
_space_group_name_H-M_alt 'P 1'
loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_atom_site_occupancy
Na1 Na 0 0 0 1
Cl1 Cl 0.5 0.5 0.5 1
"""


if __name__ == "__main__":
    unittest.main()
