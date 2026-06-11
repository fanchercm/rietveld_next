"""Tests for residual vector kernels."""

from __future__ import annotations

import math
import unittest

from rietveld_next.optimization import residual_vector


class ResidualVectorTests(unittest.TestCase):
    """Known-value and validation tests for residual vectors."""

    def test_unweighted_residual_vector(self) -> None:
        self.assertEqual(
            residual_vector([10.0, 12.0, 9.5], [9.0, 13.0, 9.0]),
            [1.0, -1.0, 0.5],
        )

    def test_weighted_residual_vector(self) -> None:
        self.assertEqual(
            residual_vector([10.0, 12.0, 9.5], [9.0, 13.0, 9.0], [2.0, 0.5, 0.25]),
            [0.5, -2.0, 2.0],
        )

    def test_empty_residual_vector(self) -> None:
        self.assertEqual(residual_vector([], []), [])

    def test_residual_vector_rejects_length_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "same length"):
            residual_vector([1.0], [1.0, 2.0])

    def test_residual_vector_rejects_non_positive_sigma(self) -> None:
        with self.assertRaisesRegex(ValueError, "sigma\\[1\\] must be positive"):
            residual_vector([1.0, 2.0], [1.0, 2.0], [1.0, 0.0])

    def test_residual_vector_rejects_non_finite_observed_value(self) -> None:
        with self.assertRaisesRegex(ValueError, "observed\\[0\\] must be a finite number"):
            residual_vector([math.nan], [1.0])


if __name__ == "__main__":
    unittest.main()
