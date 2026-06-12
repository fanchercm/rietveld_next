"""Tests for M34 validation baseline helpers."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from rietveld_next.validation import (
    ComparisonHarness,
    ReleaseChecklist,
    TolerancePolicy,
    ValidationCase,
    ValidationReport,
    check_markdown_links,
    create_synthetic_profile_dataset,
    package_import_smoke_test,
    validation_ci_matrix,
)


class ValidationBaselineTests(unittest.TestCase):
    """Unit tests for deterministic validation support."""

    def test_synthetic_profile_dataset_is_deterministic(self) -> None:
        first = create_synthetic_profile_dataset(5)
        second = create_synthetic_profile_dataset(5)

        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.y, (0.0, 0.5, 1.0, 0.5, 0.0))

    def test_synthetic_profile_dataset_rejects_too_few_samples(self) -> None:
        with self.assertRaisesRegex(ValueError, "sample_count"):
            create_synthetic_profile_dataset(2)

    def test_validation_report_summarizes_pass_fail_and_expensive_cases(self) -> None:
        tolerance = TolerancePolicy(absolute=0.01, relative=0.0, units="relative_intensity", rationale="Synthetic smoke.")
        report = ValidationReport(
            cases=(
                ValidationCase("case_pass", "synthetic_profile_5", expected=1.0, observed=1.005, tolerance=tolerance),
                ValidationCase(
                    "case_fail",
                    "synthetic_profile_5",
                    expected=1.0,
                    observed=1.1,
                    tolerance=tolerance,
                    expensive=True,
                ),
            ),
            known_limitations=("No cross-software reference data in smoke tests.",),
        )

        data = report.to_dict()

        self.assertFalse(report.passed)
        self.assertEqual(data["summary"], {"total": 2, "passed": 1, "failed": 1, "expensive": 1})
        self.assertEqual(data["known_limitations"], ["No cross-software reference data in smoke tests."])

    def test_comparison_harness_placeholders_do_not_execute_external_backends(self) -> None:
        harness = ComparisonHarness("FullProf", placeholder_reason="No redistributable fixture is bundled.")

        result = harness.dry_run()

        self.assertEqual(result.status, "placeholder")
        self.assertIn("No redistributable", result.message)

    def test_import_smoke_test_imports_packages(self) -> None:
        imported = package_import_smoke_test(("rietveld_next.core", "rietveld_next.validation"))

        self.assertEqual(imported, ("rietveld_next.core", "rietveld_next.validation"))

    def test_ci_matrix_documents_cross_platform_targets(self) -> None:
        matrix = validation_ci_matrix()

        self.assertIn({"os": "ubuntu-latest", "python": "3.12"}, matrix)
        self.assertIn({"os": "windows-latest", "python": "3.12"}, matrix)

    def test_markdown_link_checker_reports_missing_local_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docs = root / "docs"
            docs.mkdir()
            page = docs / "page.md"
            page.write_text("[missing](missing.md)\n[anchor](#local)\n[web](https://example.invalid)\n", encoding="utf-8")

            issues = check_markdown_links(root, (page,))

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].target, "missing.md")

    def test_release_checklist_reports_missing_items(self) -> None:
        checklist = ReleaseChecklist(
            required_checks=("tests", "schema", "docs"),
            completed_checks=("tests", "docs"),
        )

        self.assertFalse(checklist.ready)
        self.assertEqual(checklist.missing_checks, ("schema",))


if __name__ == "__main__":
    unittest.main()
