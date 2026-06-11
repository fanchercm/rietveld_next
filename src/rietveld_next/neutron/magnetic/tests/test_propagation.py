"""Tests for magnetic propagation vector entities."""

from __future__ import annotations

import math
import unittest

from rietveld_next.neutron.magnetic import PropagationVector


class PropagationVectorTests(unittest.TestCase):
    """Validate reciprocal-space units, serialization, and phase convention."""

    def test_propagation_vector_phase_and_serialization_are_explicit(self) -> None:
        vector = PropagationVector("k1", (0.5, 0.0, 0.25))

        self.assertEqual(vector.phase_turns((1.0, 0.0, 2.0)), 1.0)
        self.assertAlmostEqual(vector.phase_radians((1.0, 0.0, 2.0)), 2.0 * math.pi)
        self.assertEqual(
            vector.to_dict(),
            {
                "vector_id": "k1",
                "units": "reciprocal_lattice_units",
                "coordinate_frame": "reciprocal_lattice_fractional",
                "components_rlu": [0.5, 0.0, 0.25],
            },
        )

    def test_propagation_vector_round_trip_from_dict(self) -> None:
        vector = PropagationVector.from_dict(
            {
                "vector_id": "k2",
                "components_rlu": [0.0, 0.5, 0.0],
                "coordinate_frame": "reciprocal_lattice_fractional",
            }
        )

        self.assertEqual(vector.vector_id, "k2")
        self.assertEqual(vector.components_rlu, (0.0, 0.5, 0.0))

    def test_propagation_vector_rejects_wrong_vector_length(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly three"):
            PropagationVector("k1", (0.5, 0.0))

    def test_propagation_vector_rejects_non_finite_component(self) -> None:
        with self.assertRaisesRegex(ValueError, "components_rlu\\[1\\]"):
            PropagationVector("k1", (0.5, math.nan, 0.0))

    def test_propagation_vector_rejects_unknown_coordinate_frame(self) -> None:
        with self.assertRaisesRegex(ValueError, "coordinate_frame"):
            PropagationVector("k1", (0.0, 0.0, 0.0), coordinate_frame="cartesian")

    def test_phase_rejects_invalid_fractional_position(self) -> None:
        vector = PropagationVector("k1", (0.5, 0.0, 0.0))

        with self.assertRaisesRegex(ValueError, "fractional_position"):
            vector.phase_turns((1.0, 0.0, math.inf))


if __name__ == "__main__":
    unittest.main()
