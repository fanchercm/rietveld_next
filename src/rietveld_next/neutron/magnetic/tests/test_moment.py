"""Tests for magnetic moment entities."""

from __future__ import annotations

import math
import unittest

from rietveld_next.neutron.magnetic import MagneticMoment


class MagneticMomentTests(unittest.TestCase):
    """Validate moment units, serialization, and vector shape."""

    def test_moment_magnitude_and_serialization_are_explicit(self) -> None:
        moment = MagneticMoment("mn1", (1.0, 2.0, 2.0), coordinate_frame="cartesian_sample")

        self.assertEqual(moment.magnitude_bohr_magneton, 3.0)
        self.assertEqual(
            moment.to_dict(),
            {
                "site_id": "mn1",
                "units": "bohr_magneton",
                "coordinate_frame": "cartesian_sample",
                "components_bohr_magneton": [1.0, 2.0, 2.0],
                "magnitude_bohr_magneton": 3.0,
            },
        )

    def test_moment_round_trip_from_dict(self) -> None:
        moment = MagneticMoment.from_dict(
            {
                "site_id": "fe1",
                "components_bohr_magneton": [0.0, 0.0, 4.1],
                "coordinate_frame": "crystal_fractional",
                "magnitude_bohr_magneton": 4.1,
            }
        )

        self.assertEqual(moment.site_id, "fe1")
        self.assertEqual(moment.components_bohr_magneton, (0.0, 0.0, 4.1))

    def test_moment_validate_magnitude_accepts_explicit_bounds(self) -> None:
        moment = MagneticMoment("mn1", (1.0, 2.0, 2.0))

        self.assertIsNone(
            moment.validate_magnitude(
                min_bohr_magneton=2.5,
                max_bohr_magneton=3.5,
            )
        )

    def test_moment_validate_magnitude_rejects_out_of_bounds_value(self) -> None:
        moment = MagneticMoment("mn1", (1.0, 2.0, 2.0))

        with self.assertRaisesRegex(ValueError, "exceeds the maximum"):
            moment.validate_magnitude(max_bohr_magneton=2.9)

    def test_moment_validate_magnitude_rejects_invalid_bounds(self) -> None:
        moment = MagneticMoment("mn1", (1.0, 2.0, 2.0))

        with self.assertRaisesRegex(ValueError, "greater than or equal"):
            moment.validate_magnitude(min_bohr_magneton=4.0, max_bohr_magneton=3.0)

    def test_moment_from_dict_rejects_inconsistent_magnitude(self) -> None:
        with self.assertRaisesRegex(ValueError, "Euclidean norm"):
            MagneticMoment.from_dict(
                {
                    "site_id": "fe1",
                    "components_bohr_magneton": [0.0, 0.0, 4.1],
                    "magnitude_bohr_magneton": 4.2,
                }
            )

    def test_moment_rejects_wrong_vector_length(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly three"):
            MagneticMoment("mn1", (1.0, 2.0))

    def test_moment_rejects_non_finite_component(self) -> None:
        with self.assertRaisesRegex(ValueError, "components_bohr_magneton\\[2\\]"):
            MagneticMoment("mn1", (1.0, 2.0, math.inf))

    def test_moment_rejects_unknown_coordinate_frame(self) -> None:
        with self.assertRaisesRegex(ValueError, "coordinate_frame"):
            MagneticMoment("mn1", (0.0, 0.0, 1.0), coordinate_frame="sample")


if __name__ == "__main__":
    unittest.main()
