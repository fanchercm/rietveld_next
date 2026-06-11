"""Tests for benchmark taxonomy and naming helpers."""

from __future__ import annotations

import unittest

from rietveld_next.benchmarks.taxonomy import (
    BenchmarkKind,
    benchmark_families,
    build_benchmark_id,
    parse_benchmark_id,
)


class BenchmarkTaxonomyTests(unittest.TestCase):
    """Validation tests for benchmark ID conventions."""

    def test_benchmark_id_includes_required_components(self) -> None:
        benchmark_id = build_benchmark_id(
            workstream="numerical",
            kernel="gaussian_profile",
            backend="rust",
            size="small",
            variant="synthetic",
        )

        self.assertEqual(benchmark_id, "numerical.gaussian_profile.rust.small.synthetic")
        parsed = parse_benchmark_id(benchmark_id)
        self.assertEqual(parsed.backend, "rust")
        self.assertEqual(parsed.to_dict()["benchmark_id"], benchmark_id)

    def test_taxonomy_distinguishes_required_benchmark_kinds(self) -> None:
        kinds = {family.kind for family in benchmark_families().values()}

        self.assertIn(BenchmarkKind.MICRO, kinds)
        self.assertIn(BenchmarkKind.INTEGRATION, kinds)
        self.assertIn(BenchmarkKind.SCIENTIFIC_VALIDATION, kinds)
        self.assertIn(BenchmarkKind.END_TO_END_WORKFLOW, kinds)

    def test_only_micro_numerical_family_is_default_ci(self) -> None:
        default_ci_families = [name for name, family in benchmark_families().items() if family.default_ci]

        self.assertEqual(default_ci_families, ["numerical_micro"])

    def test_parse_rejects_missing_component(self) -> None:
        with self.assertRaisesRegex(ValueError, "workstream.kernel.backend.size.variant"):
            parse_benchmark_id("numerical.gaussian_profile.python.small")

    def test_build_rejects_invalid_slug(self) -> None:
        with self.assertRaisesRegex(ValueError, "backend"):
            build_benchmark_id(
                workstream="numerical",
                kernel="gaussian_profile",
                backend="Rust",
                size="small",
                variant="synthetic",
            )


if __name__ == "__main__":
    unittest.main()
