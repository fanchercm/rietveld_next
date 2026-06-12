"""Tests for magnetic import skeletons."""

from __future__ import annotations

import unittest

from rietveld_next.neutron.magnetic import (
    RepresentationAnalysisImportPlaceholder,
    create_representation_analysis_placeholder,
    parse_magnetic_cif_skeleton,
)


class MagneticImportTests(unittest.TestCase):
    """Validate deterministic mCIF and representation-analysis placeholders."""

    def test_parse_magnetic_cif_reports_supported_and_unsupported_fields(self) -> None:
        result = parse_magnetic_cif_skeleton(
            """
            data_mn_oxide
            _cell_length_a 5.0
            _cell_angle_alpha 90
            _magnetic_space_group_name_BNS "P 1"
            _atom_site_label Mn1
            loop_
            _atom_site_fract_x
            0.0
            """
        )

        self.assertEqual(result.data_block, "mn_oxide")
        self.assertEqual(
            result.supported_fields,
            {
                "_cell_angle_alpha": "90",
                "_cell_length_a": "5.0",
                "_magnetic_space_group_name_bns": "P 1",
            },
        )
        self.assertEqual(
            result.unsupported_fields,
            ("_atom_site_label", "loop_", "_atom_site_fract_x"),
        )
        self.assertIn("scalar-field skeleton", result.warnings[0])
        self.assertEqual(result.to_dict()["schema_version"], "m24-mcif-skeleton-v1")

    def test_parse_magnetic_cif_rejects_duplicate_supported_scalar_field(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicated"):
            parse_magnetic_cif_skeleton(
                """
                data_duplicate
                _cell_length_a 5.0
                _cell_length_a 6.0
                """
            )

    def test_parse_magnetic_cif_rejects_malformed_scalar_line(self) -> None:
        with self.assertRaisesRegex(ValueError, "tag-value"):
            parse_magnetic_cif_skeleton("data_bad\nnot_a_tag")

    def test_parse_magnetic_cif_rejects_invalid_cell_bounds(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive in angstroms"):
            parse_magnetic_cif_skeleton("data_bad\n_cell_length_a -1.0")
        with self.assertRaisesRegex(ValueError, "less than 180 degrees"):
            parse_magnetic_cif_skeleton("data_bad\n_cell_angle_alpha 180")

    def test_representation_analysis_placeholder_records_extension_contract(self) -> None:
        placeholder = create_representation_analysis_placeholder(
            {
                "source_tool": "BasIreps",
                "source_version": "synthetic",
                "irrep_labels": ["G1", "G3"],
                "basis_vector_count": 4,
            }
        )

        self.assertIsInstance(placeholder, RepresentationAnalysisImportPlaceholder)
        self.assertEqual(placeholder.status, "placeholder")
        self.assertEqual(placeholder.irrep_labels, ("G1", "G3"))
        self.assertEqual(placeholder.basis_vector_count, 4)
        self.assertIn("basis_vectors", placeholder.extension_contract)
        self.assertEqual(placeholder.to_dict()["source_tool"], "BasIreps")

    def test_representation_analysis_placeholder_rejects_bad_payload(self) -> None:
        with self.assertRaisesRegex(ValueError, "source_tool"):
            create_representation_analysis_placeholder({"basis_vector_count": 1})
        with self.assertRaisesRegex(ValueError, "non-negative"):
            create_representation_analysis_placeholder(
                {"source_tool": "SARAh", "basis_vector_count": -1}
            )


if __name__ == "__main__":
    unittest.main()
