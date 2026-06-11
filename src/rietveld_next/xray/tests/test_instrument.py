"""Tests for continuous-wave X-ray instrument metadata models."""

from __future__ import annotations

import math
import unittest

from rietveld_next.xray import (
    LabCwXrdInstrument,
    SynchrotronCwXrdInstrument,
    WavelengthMetadata,
    validate_wavelength_metadata,
)


class XrayInstrumentMetadataTests(unittest.TestCase):
    """Validate lab and synchrotron metadata boundaries."""

    def test_lab_instrument_distinguishes_lab_specific_metadata(self) -> None:
        wavelength = WavelengthMetadata(
            1.5406,
            label="Cu Kalpha1",
            uncertainty_angstrom=0.0001,
            provenance="synthetic lab calibration",
        )
        instrument = LabCwXrdInstrument(
            "lab-diffractometer",
            wavelength,
            tube_anode="Cu",
            radiation_line="Kalpha1",
            generator_voltage_kv=40,
            generator_current_ma=30.0,
        )

        self.assertEqual(instrument.instrument_type, "lab_cw_xrd")
        self.assertEqual(instrument.wavelength_metadata.wavelength_angstrom, 1.5406)
        self.assertEqual(instrument.generator_voltage_kv, 40.0)
        self.assertEqual(
            instrument.to_dict(),
            {
                "instrument_type": "lab_cw_xrd",
                "name": "lab-diffractometer",
                "wavelength_metadata": {
                    "wavelength_angstrom": 1.5406,
                    "units": "angstrom",
                    "label": "Cu Kalpha1",
                    "uncertainty_angstrom": 0.0001,
                    "provenance": "synthetic lab calibration",
                },
                "tube_anode": "Cu",
                "radiation_line": "Kalpha1",
                "goniometer_geometry": "bragg-brentano",
                "units": {
                    "wavelength": "angstrom",
                    "generator_voltage": "kV",
                    "generator_current": "mA",
                },
                "generator_voltage_kv": 40.0,
                "generator_current_ma": 30.0,
            },
        )

    def test_synchrotron_instrument_requires_beamline_metadata(self) -> None:
        wavelength = WavelengthMetadata(0.7995, label="monochromatic")
        instrument = SynchrotronCwXrdInstrument(
            "powder-station",
            wavelength,
            facility_name="Example Light Source",
            beamline_name="BL-1",
            monochromator="Si(111)",
            storage_ring_mode="top-up",
        )

        self.assertEqual(instrument.instrument_type, "synchrotron_cw_xrd")
        self.assertEqual(
            instrument.to_dict(),
            {
                "instrument_type": "synchrotron_cw_xrd",
                "name": "powder-station",
                "wavelength_metadata": {
                    "wavelength_angstrom": 0.7995,
                    "units": "angstrom",
                    "label": "monochromatic",
                },
                "facility_name": "Example Light Source",
                "beamline_name": "BL-1",
                "units": {"wavelength": "angstrom"},
                "monochromator": "Si(111)",
                "storage_ring_mode": "top-up",
            },
        )

    def test_wavelength_metadata_validation_reports_missing_metadata(self) -> None:
        self.assertEqual(
            validate_wavelength_metadata(None),
            ("wavelength_metadata is required; provide wavelength_angstrom in angstroms.",),
        )

    def test_instrument_construction_rejects_missing_wavelength(self) -> None:
        with self.assertRaisesRegex(ValueError, "wavelength_metadata is required"):
            LabCwXrdInstrument("lab-diffractometer", None, tube_anode="Cu")  # type: ignore[arg-type]

    def test_synchrotron_construction_rejects_missing_beamline(self) -> None:
        with self.assertRaisesRegex(ValueError, "beamline_name is required"):
            SynchrotronCwXrdInstrument(
                "powder-station",
                WavelengthMetadata(0.7995),
                facility_name="Example Light Source",
                beamline_name="",
            )

    def test_wavelength_metadata_rejects_invalid_uncertainty(self) -> None:
        with self.assertRaisesRegex(ValueError, "uncertainty_angstrom must be positive"):
            WavelengthMetadata(1.5406, uncertainty_angstrom=0.0)

    def test_wavelength_metadata_rejects_non_finite_wavelength(self) -> None:
        with self.assertRaisesRegex(ValueError, "wavelength_angstrom must be a finite number"):
            WavelengthMetadata(math.inf)

    def test_lab_instrument_rejects_non_positive_generator_current(self) -> None:
        with self.assertRaisesRegex(ValueError, "generator_current_ma must be positive"):
            LabCwXrdInstrument(
                "lab-diffractometer",
                WavelengthMetadata(1.5406),
                tube_anode="Cu",
                generator_current_ma=-1.0,
            )

    def test_synchrotron_optional_metadata_cannot_be_empty(self) -> None:
        with self.assertRaisesRegex(ValueError, "monochromator must be a non-empty string"):
            SynchrotronCwXrdInstrument(
                "powder-station",
                WavelengthMetadata(0.7995),
                facility_name="Example Light Source",
                beamline_name="BL-1",
                monochromator=" ",
            )


if __name__ == "__main__":
    unittest.main()
