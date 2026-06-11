"""Tests for repository boundary checks."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rietveld_next.core.architecture import check_repository_boundaries


class RepositoryBoundaryTests(unittest.TestCase):
    """Validate source-layout and dependency-boundary checks."""

    def test_current_repository_satisfies_boundary_checks(self) -> None:
        root = Path(__file__).resolve().parents[5]

        report = check_repository_boundaries(root)

        self.assertTrue(report.ok, [issue.__dict__ for issue in report.issues])

    def test_forbidden_top_level_directory_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "docs").mkdir()
            (root / "docs" / "PACKAGE_TREE.md").write_text("# Package Tree\n", encoding="utf-8")
            (root / "src" / "rietveld_next").mkdir(parents=True)
            (root / "tests").mkdir()

            report = check_repository_boundaries(root)

        self.assertFalse(report.ok)
        self.assertEqual(report.issues[0].code, "forbidden_top_level_directory")
        self.assertEqual(report.issues[0].path, "tests")

    def test_disallowed_core_import_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "docs").mkdir()
            (root / "docs" / "PACKAGE_TREE.md").write_text("# Package Tree\n", encoding="utf-8")
            module_dir = root / "src" / "rietveld_next" / "core"
            module_dir.mkdir(parents=True)
            (module_dir / "bad.py").write_text("from rietveld_next.ai import tools\n", encoding="utf-8")

            report = check_repository_boundaries(root)

        self.assertFalse(report.ok)
        self.assertEqual(report.issues[0].code, "disallowed_import")
        self.assertEqual(report.issues[0].path, "src/rietveld_next/core/bad.py")

    def test_disallowed_root_import_member_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "docs").mkdir()
            (root / "docs" / "PACKAGE_TREE.md").write_text("# Package Tree\n", encoding="utf-8")
            module_dir = root / "src" / "rietveld_next" / "core"
            module_dir.mkdir(parents=True)
            (module_dir / "bad.py").write_text("from rietveld_next import ai\n", encoding="utf-8")

            report = check_repository_boundaries(root)

        self.assertFalse(report.ok)
        self.assertEqual(report.issues[0].code, "disallowed_import")
        self.assertEqual(report.issues[0].path, "src/rietveld_next/core/bad.py")

    def test_disallowed_relative_import_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "docs").mkdir()
            (root / "docs" / "PACKAGE_TREE.md").write_text("# Package Tree\n", encoding="utf-8")
            module_dir = root / "src" / "rietveld_next" / "core"
            module_dir.mkdir(parents=True)
            (module_dir / "bad.py").write_text("from ..ai import tools\n", encoding="utf-8")

            report = check_repository_boundaries(root)

        self.assertFalse(report.ok)
        self.assertEqual(report.issues[0].code, "disallowed_import")
        self.assertEqual(report.issues[0].path, "src/rietveld_next/core/bad.py")

    def test_disallowed_relative_member_import_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "docs").mkdir()
            (root / "docs" / "PACKAGE_TREE.md").write_text("# Package Tree\n", encoding="utf-8")
            module_dir = root / "src" / "rietveld_next" / "core"
            module_dir.mkdir(parents=True)
            (module_dir / "bad.py").write_text("from .. import ai\n", encoding="utf-8")

            report = check_repository_boundaries(root)

        self.assertFalse(report.ok)
        self.assertEqual(report.issues[0].code, "disallowed_import")
        self.assertEqual(report.issues[0].path, "src/rietveld_next/core/bad.py")


if __name__ == "__main__":
    unittest.main()
