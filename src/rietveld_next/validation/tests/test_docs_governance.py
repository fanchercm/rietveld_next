"""Tests for M35 documentation and governance artifacts."""

from __future__ import annotations

from pathlib import Path
import unittest

from rietveld_next.validation import check_markdown_links


class DocumentationGovernanceTests(unittest.TestCase):
    """Validate required M35 documentation artifacts."""

    def test_m35_required_docs_exist_and_are_actionable(self) -> None:
        root = Path(__file__).resolve().parents[4]
        required = {
            "docs/architecture_overview.md": ("Purpose", "Scope", "Non-Goals", "Related Files"),
            "docs/numerical_engine_theory.md": ("Purpose", "Scope", "Non-Goals", "Example"),
            "docs/tof_refinement_guide.md": ("Purpose", "Scope", "Non-Goals", "Example"),
            "docs/neutron_refinement_guide.md": ("Purpose", "Scope", "Non-Goals", "Example"),
            "docs/magnetic_refinement_guide.md": ("Purpose", "Scope", "Non-Goals", "Example"),
            "docs/edxrd_guide.md": ("Purpose", "Scope", "Non-Goals", "Example"),
            "docs/ai_refinement_guide.md": ("Purpose", "Scope", "Non-Goals", "Example"),
            "docs/hpc_deployment_guide.md": ("Purpose", "Scope", "Non-Goals", "Example"),
            "docs/plugin_developer_guide.md": ("Purpose", "Scope", "Non-Goals", "Example"),
            "docs/benchmark_guide.md": ("Purpose", "Scope", "Non-Goals", "Example"),
            "docs/validation_guide.md": ("Purpose", "Scope", "Non-Goals", "Example"),
            "docs/contributing.md": ("Purpose", "Scope", "Non-Goals", "Workflow"),
            "docs/code_of_conduct.md": ("Purpose", "Scope", "Non-Goals", "Expectations"),
            "docs/governance_charter.md": ("Purpose", "Scope", "Non-Goals", "Decision Rules"),
            "docs/license_and_citation.md": ("Purpose", "Scope", "Non-Goals", "Citation Guidance"),
            "docs/release_process.md": ("Purpose", "Scope", "Non-Goals", "Checklist"),
            "docs/roadmap.md": ("Purpose", "Scope", "Non-Goals", "Milestone Themes"),
            "docs/m35_completion_report.md": ("Issue Closure Map", "Validation"),
        }

        for relative_path, required_terms in required.items():
            path = root / relative_path
            self.assertTrue(path.is_file(), relative_path)
            text = path.read_text(encoding="utf-8")
            for term in required_terms:
                self.assertIn(term, text, f"{relative_path} missing {term!r}")

    def test_m35_docs_have_valid_local_links(self) -> None:
        root = Path(__file__).resolve().parents[4]
        docs = tuple(sorted((root / "docs").glob("*.md")))

        issues = check_markdown_links(root, docs)

        self.assertEqual(issues, ())


if __name__ == "__main__":
    unittest.main()
