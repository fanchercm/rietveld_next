"""Tests for deterministic physics proxy benchmark helpers."""

from __future__ import annotations

import unittest

from rietveld_next.benchmarks.physics_proxies import (
    run_edxrd_detector_response_proxy_benchmark,
    run_magnetic_structure_factor_proxy_benchmark,
    run_multi_bank_tof_profile_proxy_benchmark,
    run_neutron_scattering_lookup_proxy_benchmark,
)
from rietveld_next.benchmarks.results import validate_benchmark_result_dict


class PhysicsProxyBenchmarkTests(unittest.TestCase):
    """Smoke and metadata tests for issue-scoped physics proxy benchmarks."""

    def test_multi_bank_tof_profile_proxy_reports_bank_metadata(self) -> None:
        result = run_multi_bank_tof_profile_proxy_benchmark(
            bank_count=2,
            bins_per_bank=16,
            reflection_count=2,
        )

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.name, "multi_bank_tof_profile_proxy")
        self.assertEqual(result.input_size, 32)
        self.assertEqual(result.environment["bank_count"], 2)
        self.assertEqual(len(result.environment["banks"]), 2)
        self.assertIn("calibration", result.environment["banks"][0])
        self.assertGreaterEqual(result.environment["banks"][0]["runtime_seconds"], 0.0)
        self.assertGreater(result.checksum or 0.0, 0.0)
        self.assertIn("synthetic proxy", result.environment["assumptions"]["validation_status"])
        self.assertEqual(result.environment["device"], "cpu")
        validate_benchmark_result_dict(result.to_dict())

    def test_multi_bank_tof_proxy_requires_at_least_two_banks(self) -> None:
        with self.assertRaisesRegex(ValueError, "bank_count"):
            run_multi_bank_tof_profile_proxy_benchmark(bank_count=1)

    def test_neutron_lookup_proxy_records_known_values(self) -> None:
        result = run_neutron_scattering_lookup_proxy_benchmark(lookup_count=8)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.input_size, 8)
        self.assertAlmostEqual(
            result.environment["known_values"]["1H_bound_coherent_fm"],
            -3.7406,
            places=4,
        )
        self.assertIn("2H", result.environment["unique_result_isotopes"])
        self.assertIn("NIST", result.environment["source"])
        validate_benchmark_result_dict(result.to_dict())

    def test_neutron_lookup_cached_variant_is_deterministic(self) -> None:
        first = run_neutron_scattering_lookup_proxy_benchmark(
            lookup_count=8,
            use_cached_keys=True,
        )
        second = run_neutron_scattering_lookup_proxy_benchmark(
            lookup_count=8,
            use_cached_keys=True,
        )

        self.assertEqual(first.name, "neutron_scattering_length_lookup_proxy_cached_keys")
        self.assertEqual(first.checksum, second.checksum)

    def test_magnetic_structure_factor_proxy_has_stable_checksum(self) -> None:
        result = run_magnetic_structure_factor_proxy_benchmark(reflection_count=4)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.input_size, 4)
        self.assertEqual(len(result.environment["reflection_checksums"]), 4)
        self.assertAlmostEqual(result.checksum or 0.0, 167.2014479877663, places=10)
        self.assertIn("not a full magnetic", result.environment["assumptions"]["magnetic_model"])
        validate_benchmark_result_dict(result.to_dict())

    def test_magnetic_structure_factor_proxy_rejects_invalid_reflection_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "reflection_count"):
            run_magnetic_structure_factor_proxy_benchmark(reflection_count=0)

    def test_edxrd_detector_response_proxy_reports_shape_and_variant(self) -> None:
        result = run_edxrd_detector_response_proxy_benchmark(
            channel_count=32,
            peak_count=2,
        )

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.input_size, 32)
        self.assertEqual(result.environment["detector_response_variant"], "gaussian")
        self.assertTrue(result.environment["finite_output"])
        self.assertEqual(result.environment["response_sample_count"], 32)
        self.assertEqual(result.environment["calibration_metadata"]["axis_type"], "energy")
        validate_benchmark_result_dict(result.to_dict())

    def test_edxrd_detector_response_tail_variant_changes_checksum(self) -> None:
        gaussian = run_edxrd_detector_response_proxy_benchmark(
            channel_count=32,
            peak_count=2,
        )
        with_tail = run_edxrd_detector_response_proxy_benchmark(
            channel_count=32,
            peak_count=2,
            include_tail=True,
        )

        self.assertEqual(with_tail.environment["detector_response_variant"], "gaussian_with_tail")
        self.assertGreater(with_tail.checksum or 0.0, gaussian.checksum or 0.0)


if __name__ == "__main__":
    unittest.main()
