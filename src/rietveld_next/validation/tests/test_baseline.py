"""Tests for M34 validation baseline helpers."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from rietveld_next.validation import (
    ComparisonHarness,
    PerformanceRegressionThreshold,
    ReleaseChecklist,
    SecurityScanPolicy,
    TolerancePolicy,
    ValidationCase,
    ValidationReport,
    VisualRegressionSnapshot,
    check_markdown_links,
    compare_performance_regression,
    create_synthetic_profile_dataset,
    fullprof_comparison_placeholder,
    gsasii_comparison_harness,
    package_import_smoke_test,
    standard_release_checklist,
    topas_comparison_placeholder,
    validate_golden_dataset_dict,
    validate_validation_report_dict,
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
        validate_validation_report_dict(data)

    def test_validation_report_dict_rejects_empty_case_objects(self) -> None:
        report = ValidationReport(cases=()).to_dict()
        report["cases"] = [{}]
        report["summary"] = {"total": 1, "passed": 0, "failed": 1, "expensive": 0}

        with self.assertRaisesRegex(ValueError, "missing required keys"):
            validate_validation_report_dict(report)

    def test_golden_dataset_dict_validator_rejects_schema_mismatch(self) -> None:
        data = create_synthetic_profile_dataset(5).to_dict()
        validate_golden_dataset_dict(data)
        data["schema_version"] = "wrong"

        with self.assertRaisesRegex(ValueError, "unsupported"):
            validate_golden_dataset_dict(data)

    def test_comparison_harness_placeholders_do_not_execute_external_backends(self) -> None:
        harness = fullprof_comparison_placeholder()

        result = harness.dry_run()

        self.assertEqual(result.status, "placeholder")
        self.assertIn("not bundled", result.message)

    def test_gsasii_harness_is_explicit_offline_or_dry_run(self) -> None:
        offline = gsasii_comparison_harness().dry_run()
        configured = gsasii_comparison_harness(("python", "compare_gsasii.py")).dry_run()

        self.assertEqual(offline.backend, "GSAS-II")
        self.assertEqual(offline.status, "placeholder")
        self.assertEqual(configured.status, "placeholder")
        self.assertIn("not executed", configured.message)

    def test_topas_placeholder_records_redistribution_limit(self) -> None:
        result = topas_comparison_placeholder().dry_run()

        self.assertEqual(result.status, "placeholder")
        self.assertIn("redistribution", result.message)

    def test_performance_regression_comparator_uses_explicit_thresholds(self) -> None:
        threshold = PerformanceRegressionThreshold(max_relative_slowdown=0.1, max_absolute_seconds=0.05)
        passed = compare_performance_regression(
            name="profile_smoke",
            baseline_seconds=1.0,
            current_seconds=1.03,
            threshold=threshold,
        )
        failed = compare_performance_regression(
            name="profile_smoke",
            baseline_seconds=1.0,
            current_seconds=1.2,
            threshold=threshold,
        )

        self.assertTrue(passed.passed)
        self.assertFalse(failed.passed)

    def test_visual_regression_snapshot_validates_dimensions_and_checksum(self) -> None:
        snapshot = VisualRegressionSnapshot(
            view_id="parameter_table",
            width_px=800,
            height_px=600,
            checksum="0123456789abcdef",
        )

        self.assertEqual(snapshot.to_dict()["view_id"], "parameter_table")
        with self.assertRaisesRegex(ValueError, "checksum"):
            VisualRegressionSnapshot("bad", 800, 600, "not-hex")

    def test_security_scan_policy_detects_secret_patterns(self) -> None:
        policy = SecurityScanPolicy()

        findings = policy.scan_text("aws_secret_access_key = test\n")

        self.assertEqual(findings, (r"aws_secret_access_key\s*=",))

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
        checklist = standard_release_checklist(completed_checks=("source-layout", "unit-tests"))

        self.assertFalse(checklist.ready)
        self.assertIn("schema-parse", checklist.missing_checks)

        custom = ReleaseChecklist(required_checks=("tests", "schema", "docs"), completed_checks=("tests", "docs"))
        self.assertEqual(custom.missing_checks, ("schema",))


if __name__ == "__main__":
    unittest.main()
