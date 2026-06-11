"""Tests for the read-only project package loader."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rietveld_next.core.model import Project
from rietveld_next.storage import (
    ProjectPackageError,
    check_project_package_integrity,
    read_project_package,
    write_project_package,
)


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


class ProjectPackageWriterTests(unittest.TestCase):
    """Validate deterministic package writes and overwrite protection."""

    def test_write_project_package_round_trips_project_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "example.rnx"
            project = Project(id="project1", experiments=[], phases=[], parameters=[])

            package = write_project_package(root, project, manifest={"format_version": "1.0.0"})

            self.assertEqual(package.project.id, "project1")
            self.assertEqual(package.manifest, {"format_version": "1.0.0"})
            self.assertEqual((root / "manifest.json").read_text(encoding="utf-8"), '{"format_version":"1.0.0"}\n')

    def test_write_project_package_refuses_to_overwrite_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project = Project(id="project1", experiments=[], phases=[], parameters=[])
            write_project_package(root, project)

            with self.assertRaisesRegex(ProjectPackageError, "Refusing to overwrite"):
                write_project_package(root, project)

    def test_write_project_package_can_overwrite_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_project_package(root, Project(id="project1", experiments=[], phases=[], parameters=[]))

            package = write_project_package(
                root,
                Project(id="project2", experiments=[], phases=[], parameters=[]),
                overwrite=True,
            )

        self.assertEqual(package.project.id, "project2")


class ProjectPackageIntegrityTests(unittest.TestCase):
    """Validate read-only project package integrity reports."""

    def test_integrity_report_accepts_written_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_project_package(root, Project(id="project1", experiments=[], phases=[], parameters=[]))

            report = check_project_package_integrity(root)

        self.assertTrue(report.ok, report.issues)

    def test_integrity_report_collects_missing_project_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report = check_project_package_integrity(Path(tmpdir))

        self.assertFalse(report.ok)
        self.assertEqual(report.issues[0].code, "missing_project_metadata")

    def test_integrity_report_collects_invalid_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_project_package(root, Project(id="project1", experiments=[], phases=[], parameters=[]))
            (root / "manifest.json").write_text("[]", encoding="utf-8")

            report = check_project_package_integrity(root)

        self.assertFalse(report.ok)
        self.assertEqual(report.issues[0].code, "invalid_manifest")


if __name__ == "__main__":
    unittest.main()
