"""Tests for continuous-wave neutron instrument helpers."""

from __future__ import annotations

import unittest

from rietveld_next.neutron import (
    ConstantNeutronAbsorption,
    ContinuousWaveNeutronInstrument,
    NeutronScatterer,
)


class ContinuousWaveNeutronInstrumentTests(unittest.TestCase):
    """Validate CW neutron geometry, scattering-length, and hook behavior."""

    def test_bragg_two_theta_uses_neutron_wavelength_and_zero_shift(self) -> None:
        instrument = ContinuousWaveNeutronInstrument(
            wavelength_angstrom=1.8,
            zero_shift_degrees=0.05,
        )

        self.assertAlmostEqual(instrument.bragg_two_theta_degrees(1.8), 60.05, places=12)

    def test_nuclear_amplitude_uses_scattering_lengths_in_femtometers(self) -> None:
        instrument = ContinuousWaveNeutronInstrument(wavelength_angstrom=1.8)
        scatterers = [
            NeutronScatterer("1H", occupancy=0.5),
            NeutronScatterer("D", multiplicity=2),
        ]

        expected = 0.5 * -3.7406 + 2.0 * 6.671
        self.assertAlmostEqual(instrument.nuclear_amplitude_fm(scatterers), expected, places=12)

    def test_empty_scatterer_sequence_has_zero_amplitude(self) -> None:
        instrument = ContinuousWaveNeutronInstrument(wavelength_angstrom=1.8)

        self.assertEqual(instrument.nuclear_amplitude_fm([]), 0.0)

    def test_absorption_hook_scales_intensity_without_profile_kernel(self) -> None:
        instrument = ContinuousWaveNeutronInstrument(
            wavelength_angstrom=1.8,
            intensity_scale=2.0,
            absorption_hook=ConstantNeutronAbsorption(0.25),
        )

        self.assertEqual(instrument.absorption_transmission(), 0.25)
        self.assertEqual(instrument.scale_intensity(40.0), 20.0)

    def test_instrument_to_dict_records_units_and_hook_name(self) -> None:
        instrument = ContinuousWaveNeutronInstrument(
            wavelength_angstrom=1.8,
            absorption_hook=ConstantNeutronAbsorption(1.0),
        )

        self.assertEqual(
            instrument.to_dict(),
            {
                "instrument_type": "cw_neutron",
                "wavelength_angstrom": 1.8,
                "zero_shift_degrees": 0.0,
                "intensity_scale": 1.0,
                "absorption_hook": "ConstantNeutronAbsorption",
            },
        )

    def test_instrument_rejects_unreachable_bragg_condition(self) -> None:
        instrument = ContinuousWaveNeutronInstrument(wavelength_angstrom=3.0)

        with self.assertRaisesRegex(ValueError, "Bragg condition is unreachable"):
            instrument.bragg_two_theta_degrees(1.0)

    def test_scatterer_rejects_out_of_bounds_occupancy(self) -> None:
        with self.assertRaisesRegex(ValueError, r"\[0, 1\]"):
            NeutronScatterer("D", occupancy=1.2)

    def test_instrument_rejects_invalid_absorption_hook(self) -> None:
        with self.assertRaisesRegex(ValueError, "transmission_factor"):
            ContinuousWaveNeutronInstrument(1.8, absorption_hook=object())  # type: ignore[arg-type]

    def test_nuclear_amplitude_rejects_non_scatterer_entries(self) -> None:
        instrument = ContinuousWaveNeutronInstrument(wavelength_angstrom=1.8)

        with self.assertRaisesRegex(ValueError, "NeutronScatterer"):
            instrument.nuclear_amplitude_fm(["D"])  # type: ignore[list-item]


if __name__ == "__main__":
    unittest.main()
