"""Tests for the read-only project package loader."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rietveld_next.core.model import Project
from rietveld_next.storage import (
    ProjectImportWarning,
    ProjectImportWarningReport,
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
        self.assertTrue(package.import_warnings.ok)

    def test_read_project_package_records_missing_manifest_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "project.json").write_text(
                Project(id="project1", experiments=[], phases=[], parameters=[]).to_json(),
                encoding="utf-8",
            )

            package = read_project_package(root)

        self.assertFalse(package.import_warnings.ok)
        self.assertEqual(package.import_warnings.warnings[0].code, "missing_manifest")

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

    def test_write_project_package_supports_deterministic_gzip_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project = Project(id="project1", experiments=[], phases=[], parameters=[])

            first = write_project_package(root, project, compression="gzip")
            first_bytes = (root / "project.json.gz").read_bytes()
            second = write_project_package(root, project, overwrite=True, compression="gzip")
            second_bytes = (root / "project.json.gz").read_bytes()

        self.assertEqual(first.compression, "gzip")
        self.assertEqual(second.compression, "gzip")
        self.assertEqual(first.project_json_path.name, "project.json.gz")
        self.assertEqual(first_bytes, second_bytes)

    def test_write_project_package_rejects_ambiguous_metadata_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project = Project(id="project1", experiments=[], phases=[], parameters=[])
            write_project_package(root, project)

            with self.assertRaisesRegex(ProjectPackageError, "ambiguous package metadata"):
                write_project_package(root, project, compression="gzip")

    def test_write_project_package_rejects_unknown_compression(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(ProjectPackageError, "Unsupported project package compression"):
                write_project_package(
                    Path(tmpdir),
                    Project(id="project1", experiments=[], phases=[], parameters=[]),
                    compression="zip",  # type: ignore[arg-type]
                )


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

    def test_integrity_report_collects_ambiguous_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project = Project(id="project1", experiments=[], phases=[], parameters=[])
            write_project_package(root, project)
            write_project_package(root, project, compression="gzip", overwrite=True)
            (root / "project.json").write_text(project.to_json(), encoding="utf-8")

            report = check_project_package_integrity(root)

        self.assertFalse(report.ok)
        self.assertEqual(report.issues[0].code, "ambiguous_project_metadata")


class ProjectImportWarningReportTests(unittest.TestCase):
    """Validate deterministic import warning report formatting."""

    def test_warning_report_round_trip_json(self) -> None:
        report = ProjectImportWarningReport(
            (
                ProjectImportWarning(
                    code="missing_manifest",
                    path="manifest.json",
                    message="Optional manifest is missing.",
                ),
            )
        )

        loaded = ProjectImportWarningReport.from_json(report.to_json())

        self.assertEqual(loaded.to_json(), report.to_json())
        self.assertFalse(loaded.ok)

    def test_warning_rejects_invalid_severity(self) -> None:
        with self.assertRaisesRegex(ValueError, "severity must be 'warning'"):
            ProjectImportWarning("code", "path", "message", severity="error")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
