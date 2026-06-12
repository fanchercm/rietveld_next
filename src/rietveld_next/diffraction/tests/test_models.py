"""Tests for deterministic diffraction model helpers."""

from __future__ import annotations

import math
import unittest

import rietveld_next.diffraction as diffraction
from rietveld_next.diffraction.models import (
    ADPRecord,
    OccupancyConstraint,
    OccupancySite,
    PhaseScaleComponent,
    SyntheticReflection,
    calculate_phase_fractions,
    chebyshev_background,
    generate_reflection_ticks,
    generate_synthetic_pattern,
    isotropic_size_fwhm_degrees,
    isotropic_strain_fwhm_degrees,
    lookup_standard_reference_dataset,
    model_parameter_bounds,
    phase_scale_weight,
    polynomial_background,
    preferred_orientation_factor,
    standard_reference_dataset_registry,
    validate_adp_records,
    validate_occupancy_constraints,
)


class PreferredOrientationTests(unittest.TestCase):
    """Known-value and validation tests for preferred orientation."""

    def test_unity_ratio_returns_unit_factor(self) -> None:
        factor = preferred_orientation_factor((1, 2, 3), (0.0, 0.0, 1.0), ratio=1.0)

        self.assertAlmostEqual(factor, 1.0, places=15)

    def test_parallel_axis_matches_march_dollase_power(self) -> None:
        factor = preferred_orientation_factor((0, 0, 1), (0.0, 0.0, 2.0), ratio=2.0)

        self.assertAlmostEqual(factor, 0.125, places=15)

    def test_preferred_orientation_rejects_invalid_ratio(self) -> None:
        with self.assertRaisesRegex(ValueError, "ratio must be between"):
            preferred_orientation_factor((1, 0, 0), (1.0, 0.0, 0.0), ratio=20.0)

    def test_model_parameter_bounds_are_available(self) -> None:
        bounds = model_parameter_bounds("preferred_orientation")

        self.assertEqual(bounds[0].name, "ratio")
        self.assertEqual((bounds[0].lower, bounds[0].upper), (0.1, 10.0))


class MicrostructureBroadeningTests(unittest.TestCase):
    """Analytical and validation tests for simple broadening formulas."""

    def test_size_broadening_matches_scherrer_formula(self) -> None:
        width = isotropic_size_fwhm_degrees(
            60.0,
            wavelength_angstrom=1.5406,
            crystallite_size_angstrom=1000.0,
            shape_factor=0.9,
        )
        expected = math.degrees(0.9 * 1.5406 / (1000.0 * math.cos(math.radians(30.0))))

        self.assertAlmostEqual(width, expected, places=15)

    def test_strain_broadening_zero_microstrain_is_zero(self) -> None:
        self.assertEqual(isotropic_strain_fwhm_degrees(60.0, microstrain=0.0), 0.0)

    def test_strain_broadening_matches_formula(self) -> None:
        width = isotropic_strain_fwhm_degrees(60.0, microstrain=0.001)
        expected = math.degrees(4.0 * 0.001 * math.tan(math.radians(30.0)))

        self.assertAlmostEqual(width, expected, places=15)

    def test_broadening_rejects_invalid_inputs(self) -> None:
        with self.assertRaisesRegex(ValueError, "crystallite_size_angstrom must be positive"):
            isotropic_size_fwhm_degrees(60.0, wavelength_angstrom=1.0, crystallite_size_angstrom=0.0)
        with self.assertRaisesRegex(ValueError, "microstrain must be non-negative"):
            isotropic_strain_fwhm_degrees(60.0, microstrain=-0.1)


class BackgroundModelTests(unittest.TestCase):
    """Known-value tests for independently refinable background helpers."""

    def test_polynomial_background_evaluates_coefficients(self) -> None:
        values = polynomial_background([0.0, 1.0, 2.0], [1.0, 2.0, 1.0])

        self.assertEqual(values, [1.0, 4.0, 9.0])

    def test_polynomial_background_uses_origin_and_scale(self) -> None:
        values = polynomial_background([10.0, 12.0], [1.0, 3.0], origin=10.0, scale=2.0)

        self.assertEqual(values, [1.0, 4.0])

    def test_chebyshev_background_maps_domain_to_unit_interval(self) -> None:
        values = chebyshev_background([0.0, 1.0, 2.0], [2.0, 3.0, 4.0], domain=(0.0, 2.0))

        self.assertEqual(values, [3.0, -2.0, 9.0])

    def test_chebyshev_background_rejects_invalid_domain(self) -> None:
        with self.assertRaisesRegex(ValueError, "domain minimum"):
            chebyshev_background([0.0], [1.0], domain=(1.0, 1.0))


class SyntheticPatternTests(unittest.TestCase):
    """Tests for ticks and deterministic synthetic pattern generation."""

    def test_m15_helpers_are_exported_from_diffraction_package(self) -> None:
        reflection = diffraction.SyntheticReflection("phase-a", (1, 0, 0), 30.0, 1.0, 0.2)
        pattern = diffraction.generate_synthetic_pattern([30.0], [reflection])
        fractions = diffraction.calculate_phase_fractions([diffraction.PhaseScaleComponent("phase-a", 1.0)])

        self.assertEqual(pattern.phase_ticks[0].phase_id, "phase-a")
        self.assertEqual(fractions.fractions, {"phase-a": 1.0})
        self.assertIs(diffraction.validate_adp_records, validate_adp_records)
        self.assertIs(diffraction.validate_occupancy_constraints, validate_occupancy_constraints)

    def test_generate_reflection_ticks_sorts_and_filters(self) -> None:
        reflections = [
            SyntheticReflection("phase-b", (1, 0, 0), 30.0, 2.0, 0.2),
            SyntheticReflection("phase-a", (1, 1, 0), 20.0, 1.0, 0.2),
            SyntheticReflection("phase-a", (2, 0, 0), 40.0, 1.0, 0.2),
        ]

        ticks = generate_reflection_ticks(reflections, two_theta_range=(0.0, 35.0))

        self.assertEqual([tick.label for tick in ticks], ["(1 1 0)", "(1 0 0)"])
        self.assertEqual([tick.phase_id for tick in ticks], ["phase-a", "phase-b"])

    def test_generate_synthetic_pattern_includes_ticks_and_metadata(self) -> None:
        reflection = SyntheticReflection("phase-a", (1, 0, 0), 30.0, 2.0, 1.0)
        pattern = generate_synthetic_pattern(
            [29.0, 30.0, 31.0],
            [reflection],
            background=[10.0, 10.0, 10.0],
            phase_scales={"phase-a": 2.0},
        )

        self.assertEqual(pattern.axis_two_theta_degrees, (29.0, 30.0, 31.0))
        self.assertEqual(pattern.phase_ticks[0].label, "(1 0 0)")
        self.assertEqual(pattern.metadata["axis_unit"], "degrees two-theta")
        self.assertGreater(pattern.intensity[1], pattern.intensity[0])
        self.assertGreater(pattern.intensity[1], 10.0)

    def test_generate_synthetic_pattern_rejects_unsorted_axis(self) -> None:
        with self.assertRaisesRegex(ValueError, "sorted"):
            generate_synthetic_pattern(
                [30.0, 29.0],
                [SyntheticReflection("phase-a", (1, 0, 0), 30.0, 1.0, 0.2)],
            )


class StandardReferenceRegistryTests(unittest.TestCase):
    """Tests for deterministic reference dataset registry metadata."""

    def test_registry_entries_are_deterministic_and_synthetic_scoped(self) -> None:
        registry = standard_reference_dataset_registry()

        self.assertEqual([entry.dataset_id for entry in registry], ["synthetic-si-powder-v0", "synthetic-two-phase-v0"])
        self.assertTrue(all(entry.validation_status == "synthetic-only" for entry in registry))

    def test_lookup_standard_reference_dataset_returns_entry(self) -> None:
        entry = lookup_standard_reference_dataset("synthetic-si-powder-v0")

        self.assertEqual(entry.axis_unit, "degrees two-theta")

    def test_lookup_standard_reference_dataset_rejects_unknown_id(self) -> None:
        with self.assertRaisesRegex(KeyError, "Unsupported dataset_id"):
            lookup_standard_reference_dataset("missing")


class PhaseScaleTests(unittest.TestCase):
    """Tests for phase scale weights and fraction normalization."""

    def test_phase_scale_weight_uses_documented_proxy(self) -> None:
        component = PhaseScaleComponent(
            "phase-a",
            scale=2.0,
            formula_units_per_cell=3.0,
            molecular_mass_g_mol=4.0,
            cell_volume_angstrom3=5.0,
        )

        self.assertEqual(phase_scale_weight(component), 120.0)

    def test_calculate_phase_fractions_normalizes_weights(self) -> None:
        result = calculate_phase_fractions(
            [
                PhaseScaleComponent("phase-a", scale=2.0),
                PhaseScaleComponent("phase-b", scale=1.0, formula_units_per_cell=2.0),
            ]
        )

        self.assertEqual(result.weights, {"phase-a": 2.0, "phase-b": 2.0})
        self.assertEqual(result.fractions, {"phase-a": 0.5, "phase-b": 0.5})
        self.assertIn("weight_proxy", result.assumptions[0])

    def test_calculate_phase_fractions_rejects_zero_total(self) -> None:
        with self.assertRaisesRegex(ValueError, "At least one"):
            calculate_phase_fractions([PhaseScaleComponent("phase-a", scale=0.0)])


class OccupancyConstraintTests(unittest.TestCase):
    """Tests for structured occupancy warnings."""

    def test_validate_occupancy_constraints_reports_mismatch_and_bounds(self) -> None:
        warnings = validate_occupancy_constraints(
            [OccupancySite("site-a", 0.7), OccupancySite("site-b", 0.6), OccupancySite("site-c", 1.2)],
            [OccupancyConstraint("split-a", ("site-a", "site-b"), target_total=1.0, tolerance=0.01)],
        )

        codes = [warning.code for warning in warnings]
        self.assertIn("occupancy.constraint_mismatch", codes)
        self.assertIn("occupancy.out_of_bounds", codes)

    def test_validate_occupancy_constraints_reports_missing_site(self) -> None:
        warnings = validate_occupancy_constraints(
            [OccupancySite("site-a", 1.0)],
            [OccupancyConstraint("split-a", ("site-a", "site-b"))],
        )

        self.assertEqual(warnings[0].code, "occupancy.missing_site")
        self.assertEqual(warnings[0].severity, "error")


class ADPValidationTests(unittest.TestCase):
    """Tests for structured ADP validation warnings."""

    def test_validate_adp_records_accepts_reasonable_isotropic_and_anisotropic_values(self) -> None:
        warnings = validate_adp_records(
            [
                ADPRecord("Si1", u_iso_angstrom2=0.02),
                ADPRecord("O1", u_aniso_angstrom2=(0.02, 0.03, 0.04, 0.0, 0.0, 0.0)),
            ]
        )

        self.assertEqual(warnings, ())

    def test_validate_adp_records_reports_negative_high_missing_and_matrix_warnings(self) -> None:
        warnings = validate_adp_records(
            [
                ADPRecord("bad-u", u_iso_angstrom2=-0.01),
                ADPRecord("high-b", b_iso_angstrom2=100.0),
                ADPRecord("missing"),
                ADPRecord("bad-aniso", u_aniso_angstrom2=(0.01, 0.01, 0.01, 0.02, 0.0, 0.0)),
            ],
            u_iso_bounds_angstrom2=(0.0, 0.5),
        )

        codes = [warning.code for warning in warnings]
        self.assertIn("adp.u_iso.negative", codes)
        self.assertIn("adp.b_iso_as_u.high", codes)
        self.assertIn("adp.missing", codes)
        self.assertIn("adp.u_aniso.not_positive_definite", codes)

    def test_adp_record_rejects_malformed_anisotropic_tuple(self) -> None:
        with self.assertRaisesRegex(ValueError, "six values"):
            ADPRecord("bad", u_aniso_angstrom2=(0.01, 0.02, 0.03))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
