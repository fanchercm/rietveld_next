"""Tests for deterministic AI diagnostics and safety checks."""

from __future__ import annotations

import unittest

from rietveld_next.ai import (
    ToolContract,
    ToolField,
    classify_residual_pattern,
    detect_nonphysical_solution,
    detect_overfitting,
    detect_prompt_injection,
    evaluate_tool_call_safety,
    prompt_injection_regression_cases,
    run_prompt_injection_regression_suite,
    safety_allows,
)


class DiagnosticsSafetyTests(unittest.TestCase):
    """Validate deterministic diagnostics and fail-closed safety behavior."""

    def test_tool_contract_schema_contains_field_metadata(self) -> None:
        contract = ToolContract(
            name="diagnose",
            input_fields=("residuals",),
            output_fields=("summary",),
            description="Diagnose residuals.",
            input_schema=(ToolField("residuals", "array<float>", "Residual values.", unit="count"),),
        )

        schema = contract.to_schema()

        self.assertEqual(schema["name"], "diagnose")
        self.assertEqual(schema["inputs"][0]["unit"], "count")
        self.assertFalse(schema["requires_approval"])

    def test_residual_classifier_labels_alternating_pattern(self) -> None:
        classification = classify_residual_pattern([1.0, -1.0, 0.8, -0.7])

        self.assertIn("alternating", classification.labels)
        self.assertGreater(classification.confidence, 0.0)

    def test_nonphysical_detector_flags_bounds_and_negative_amounts(self) -> None:
        findings = detect_nonphysical_solution(
            {
                "scale": -0.1,
                "occupancy_Fe": {"value": 1.2, "lower_bound": 0.0, "upper_bound": 1.0},
                "Uiso": -0.01,
            }
        )

        codes = {finding["code"] for finding in findings}
        self.assertIn("negative_amount", codes)
        self.assertIn("above_bound", codes)
        self.assertIn("negative_displacement", codes)

    def test_overfitting_detector_flags_validation_gap(self) -> None:
        findings = detect_overfitting(
            train_rwp=8.0,
            validation_rwp=12.0,
            parameter_count=30,
            observation_count=100,
            previous_validation_rwp=10.0,
        )

        codes = {finding["code"] for finding in findings}
        self.assertIn("validation_gap", codes)
        self.assertIn("validation_regression", codes)
        self.assertIn("high_parameter_density", codes)

    def test_safety_blocks_unapproved_mutating_call(self) -> None:
        contract = ToolContract(
            name="rollback",
            input_fields=("snapshot_id", "provenance"),
            output_fields=("model_state",),
            description="Rollback state.",
            mutates_state=True,
            requires_approval=True,
        )

        findings = evaluate_tool_call_safety(contract, {"snapshot_id": "s0", "provenance": {"source": "test"}})

        self.assertFalse(safety_allows(findings))
        self.assertEqual(findings[0]["code"], "approval_required")

    def test_prompt_injection_regression_helpers_are_deterministic(self) -> None:
        cases = prompt_injection_regression_cases()
        findings = detect_prompt_injection(cases[0]["payload"])
        suite_result = run_prompt_injection_regression_suite()

        self.assertTrue(findings)
        self.assertEqual(suite_result["case_count"], 3)
        self.assertEqual(suite_result["passed_count"], 3)


if __name__ == "__main__":
    unittest.main()
