"""Tests for parameter scaling and bounded transforms."""

from __future__ import annotations

import unittest

from rietveld_next.optimization import BoundTransform, ParameterScale, scale_parameters, unscale_parameters


class TransformTests(unittest.TestCase):
    """Round-trip and validation tests for optimization transforms."""

    def test_parameter_scale_round_trip(self) -> None:
        scale = ParameterScale(offset=10.0, scale=2.0)

        self.assertEqual(scale.to_scaled(14.0), 2.0)
        self.assertEqual(scale.from_scaled(2.0), 14.0)

    def test_parameter_scale_rejects_non_positive_scale(self) -> None:
        with self.assertRaisesRegex(ValueError, "scale must be positive"):
            ParameterScale(scale=0.0)

    def test_scale_parameters_requires_matching_lengths(self) -> None:
        with self.assertRaisesRegex(ValueError, "same length"):
            scale_parameters([1.0, 2.0], [ParameterScale()])

    def test_scale_parameters_vector_round_trip(self) -> None:
        scales = [ParameterScale(offset=1.0, scale=2.0), ParameterScale(offset=-1.0, scale=4.0)]
        scaled = scale_parameters([3.0, 7.0], scales)

        self.assertEqual(scaled, [1.0, 2.0])
        self.assertEqual(unscale_parameters(scaled, scales), [3.0, 7.0])

    def test_finite_bound_transform_round_trip(self) -> None:
        transform = BoundTransform(lower=0.0, upper=10.0)
        unbounded = transform.to_unbounded(5.0)

        self.assertAlmostEqual(unbounded, 0.0, places=15)
        self.assertAlmostEqual(transform.from_unbounded(unbounded), 5.0, places=15)

    def test_one_sided_bound_transform_round_trip(self) -> None:
        transform = BoundTransform(lower=2.0)
        unbounded = transform.to_unbounded(3.0)

        self.assertAlmostEqual(transform.from_unbounded(unbounded), 3.0, places=15)

    def test_upper_bound_transform_round_trip(self) -> None:
        transform = BoundTransform(upper=5.0)
        unbounded = transform.to_unbounded(4.0)

        self.assertAlmostEqual(transform.from_unbounded(unbounded), 4.0, places=15)

    def test_lower_bound_inverse_rejects_endpoint_with_clear_message(self) -> None:
        with self.assertRaisesRegex(ValueError, "strictly greater than the lower bound"):
            BoundTransform(lower=2.0).to_unbounded(2.0)

    def test_upper_bound_inverse_rejects_endpoint_with_clear_message(self) -> None:
        with self.assertRaisesRegex(ValueError, "strictly less than the upper bound"):
            BoundTransform(upper=5.0).to_unbounded(5.0)

    def test_finite_bound_inverse_rejects_endpoint(self) -> None:
        with self.assertRaisesRegex(ValueError, "strictly inside"):
            BoundTransform(lower=0.0, upper=1.0).to_unbounded(0.0)

    def test_bound_transform_rejects_invalid_bounds(self) -> None:
        with self.assertRaisesRegex(ValueError, "lower must be less than upper"):
            BoundTransform(lower=1.0, upper=1.0)


if __name__ == "__main__":
    unittest.main()
