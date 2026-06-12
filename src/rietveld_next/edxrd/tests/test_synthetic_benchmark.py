"""Tests for the M28 EDXRD synthetic benchmark workflow."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from rietveld_next.benchmarks.results import validate_benchmark_result_dict
from rietveld_next.edxrd import (
    run_edxrd_synthetic_benchmark,
    write_edxrd_synthetic_benchmark_result,
)


class EDXRDSyntheticBenchmarkTests(unittest.TestCase):
    """Smoke tests for lightweight EDXRD synthetic benchmark output."""

    def test_synthetic_benchmark_reports_high_pressure_metadata(self) -> None:
        result = run_edxrd_synthetic_benchmark(channel_count=32)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.name, "edxrd_high_pressure_synthetic")
        self.assertEqual(result.input_size, 32)
        self.assertEqual(result.environment["axis"]["units"], "keV")
        self.assertEqual(result.environment["marker"]["pressure_gpa"], 8.0)
        self.assertEqual(result.environment["diagnostics"]["channel_count"], 32)
        self.assertIn(161, result.environment["issue_numbers"])
        self.assertGreater(result.checksum or 0.0, 0.0)
        validate_benchmark_result_dict(result.to_dict())

    def test_synthetic_benchmark_is_deterministic_except_timing(self) -> None:
        first = run_edxrd_synthetic_benchmark(channel_count=32)
        second = run_edxrd_synthetic_benchmark(channel_count=32)

        self.assertEqual(first.checksum, second.checksum)
        self.assertEqual(first.environment["peak_energies_keV"], second.environment["peak_energies_keV"])
        self.assertEqual(
            first.environment["diagnostics"]["max_abs_residual_counts"],
            second.environment["diagnostics"]["max_abs_residual_counts"],
        )

    def test_synthetic_benchmark_writes_reproducible_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "edxrd_m28_benchmark.json"

            result = write_edxrd_synthetic_benchmark_result(output_path, channel_count=16)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["name"], "edxrd_high_pressure_synthetic")
        self.assertEqual(payload["checksum"], result.checksum)
        validate_benchmark_result_dict(payload)

    def test_synthetic_benchmark_rejects_invalid_channel_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "channel_count"):
            run_edxrd_synthetic_benchmark(channel_count=0)


if __name__ == "__main__":
    unittest.main()
