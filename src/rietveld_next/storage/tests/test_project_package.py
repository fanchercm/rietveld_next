"""Tests for the read-only project package loader."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rietveld_next.core.model import Project
from rietveld_next.storage import ProjectPackageError, read_project_package


class ProjectPackageReaderTests(unittest.TestCase):
    """Validate package read success and failure modes."""

    def test_read_project_package_loads_project_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "project.json").write_text(
                Project(id="project1", experiments=[], phases=[], parameters=[]).to_json(),
                encoding="utf-8",
            )
            (root / "manifest.json").write_text('{"format_version":"1.0.0"}', encoding="utf-8")

            package = read_project_package(root)

        self.assertEqual(package.project.id, "project1")
        self.assertEqual(package.manifest, {"format_version": "1.0.0"})

    def test_read_project_package_rejects_missing_project_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(ProjectPackageError, "missing required metadata"):
                read_project_package(Path(tmpdir))

    def test_read_project_package_rejects_corrupt_project_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "project.json").write_text("{not-json", encoding="utf-8")

            with self.assertRaisesRegex(ProjectPackageError, "Failed to read valid project metadata"):
                read_project_package(root)

    def test_read_project_package_rejects_non_object_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "project.json").write_text(
                Project(id="project1", experiments=[], phases=[], parameters=[]).to_json(),
                encoding="utf-8",
            )
            (root / "manifest.json").write_text("[]", encoding="utf-8")

            with self.assertRaisesRegex(ProjectPackageError, "manifest must be a JSON object"):
                read_project_package(root)


if __name__ == "__main__":
    unittest.main()
