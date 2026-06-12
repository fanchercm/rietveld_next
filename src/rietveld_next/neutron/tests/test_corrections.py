"""Tests for neutron correction interfaces."""

from __future__ import annotations

import unittest

from rietveld_next.neutron import (
    ConstantNeutronAbsorption,
    ConstantSampleGeometryCorrection,
    ContinuousWaveNeutronInstrument,
    SimplePrimaryExtinctionCorrection,
    evaluate_extinction_correction,
    evaluate_sample_geometry_correction,
)


class NeutronCorrectionInterfaceTests(unittest.TestCase):
    """Validate sample-geometry and extinction hook boundaries."""

    def test_constant_sample_geometry_correction_validates_geometry_inputs(self) -> None:
        hook = ConstantSampleGeometryCorrection(factor=1.2, geometry="flat_plate")

        self.assertEqual(
            evaluate_sample_geometry_correction(hook, two_theta_degrees=60.0, wavelength_angstrom=1.8),
            1.2,
        )

    def test_extinction_correction_is_bounded(self) -> None:
        hook = SimplePrimaryExtinctionCorrection(coefficient_per_fm2_angstrom=0.01)

        value = evaluate_extinction_correction(hook, structure_factor_squared=4.0, wavelength_angstrom=2.0)

        self.assertAlmostEqual(value, 1.0 / 1.08)

    def test_instrument_applies_optional_correction_hooks(self) -> None:
        instrument = ContinuousWaveNeutronInstrument(
            wavelength_angstrom=1.8,
            intensity_scale=2.0,
            absorption_hook=ConstantNeutronAbsorption(0.5),
            sample_geometry_hook=ConstantSampleGeometryCorrection(1.1, geometry="capillary"),
            extinction_hook=SimplePrimaryExtinctionCorrection(0.01),
        )

        scaled = instrument.scale_intensity(
            10.0,
            two_theta_degrees=60.0,
            structure_factor_squared=4.0,
        )

        self.assertAlmostEqual(scaled, 10.0 * 2.0 * 0.5 * 1.1 / (1.0 + 0.01 * 4.0 * 1.8))
        self.assertEqual(instrument.to_dict()["sample_geometry_hook"], "ConstantSampleGeometryCorrection")
        self.assertEqual(instrument.to_dict()["extinction_hook"], "SimplePrimaryExtinctionCorrection")

    def test_instrument_requires_geometry_context_when_hook_attached(self) -> None:
        instrument = ContinuousWaveNeutronInstrument(
            wavelength_angstrom=1.8,
            sample_geometry_hook=ConstantSampleGeometryCorrection(1.0),
        )

        with self.assertRaisesRegex(ValueError, "two_theta_degrees"):
            instrument.scale_intensity(10.0)

    def test_extinction_rejects_invalid_hook_result(self) -> None:
        class BadExtinction:
            def extinction_factor(self, *, structure_factor_squared: float, wavelength_angstrom: float) -> float:
                return 1.2

        with self.assertRaisesRegex(ValueError, r"\(0, 1\]"):
            evaluate_extinction_correction(BadExtinction(), structure_factor_squared=1.0, wavelength_angstrom=1.8)


if __name__ == "__main__":
    unittest.main()
