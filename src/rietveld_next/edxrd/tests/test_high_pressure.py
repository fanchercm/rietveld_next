"""Tests for EDXRD high-pressure marker and EOS hooks."""

from __future__ import annotations

import unittest

from rietveld_next.edxrd import (
    BirchMurnaghanEquationOfState,
    EquationOfStateHook,
    HighPressureMarker,
)


class HighPressureMarkerTests(unittest.TestCase):
    """Validate high-pressure marker metadata and EOS compression."""

    def test_marker_serializes_project_entity_with_units(self) -> None:
        marker = HighPressureMarker(
            "hp-1",
            pressure_gpa=12.5,
            pressure_standard="ruby",
            temperature_kelvin=295.0,
            calibrant="Au",
            pressure_uncertainty_gpa=0.2,
            provenance={"source": "synthetic"},
        )

        payload = marker.to_project_entity()

        self.assertEqual(payload["entity_type"], "edxrd_high_pressure_marker")
        self.assertEqual(payload["units"]["pressure"], "GPa")
        self.assertEqual(payload["bounds"]["pressure_gpa"], "[0, +inf)")
        self.assertEqual(payload["provenance"]["source"], "synthetic")

    def test_marker_rejects_negative_pressure(self) -> None:
        with self.assertRaisesRegex(ValueError, "pressure_gpa must be non-negative"):
            HighPressureMarker("bad", pressure_gpa=-0.1, pressure_standard="ruby")

    def test_birch_murnaghan_pressure_matches_known_synthetic_value(self) -> None:
        eos = BirchMurnaghanEquationOfState(
            reference_volume_angstrom3=64.0,
            bulk_modulus_gpa=180.0,
            bulk_modulus_derivative=4.0,
        )

        pressure = eos.pressure_gpa(60.0)

        self.assertAlmostEqual(pressure, 13.2185086666306, places=12)
        self.assertAlmostEqual(eos.volume_at_pressure_gpa(pressure), 60.0, places=10)

    def test_eos_hook_compresses_d_spacings_isotropically(self) -> None:
        marker = HighPressureMarker("hp-2", pressure_gpa=8.0, pressure_standard="ruby")
        eos = BirchMurnaghanEquationOfState(
            reference_volume_angstrom3=64.0,
            bulk_modulus_gpa=180.0,
            bulk_modulus_derivative=4.0,
        )
        hook = EquationOfStateHook(
            eos=eos,
            reference_d_spacings_angstrom=(3.5, 3.0),
            labels=("111", "200"),
        )

        compressed = hook.compressed_d_spacings_angstrom(marker)
        prediction = hook.marker_prediction(marker)

        self.assertLess(compressed[0], 3.5)
        self.assertLess(compressed[1], 3.0)
        self.assertEqual(prediction["labels"], ["111", "200"])
        self.assertEqual(prediction["units"]["d_spacing"], "angstrom")

    def test_eos_hook_rejects_label_length_mismatch(self) -> None:
        eos = BirchMurnaghanEquationOfState(64.0, 180.0, 4.0)

        with self.assertRaisesRegex(ValueError, "labels must match"):
            EquationOfStateHook(eos=eos, reference_d_spacings_angstrom=(3.5, 3.0), labels=("111",))


if __name__ == "__main__":
    unittest.main()
