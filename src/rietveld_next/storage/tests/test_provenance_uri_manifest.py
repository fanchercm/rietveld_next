"""Tests for provenance, URI, and file manifest storage helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rietveld_next.storage import (
    FileManifestEntry,
    ProvenanceLogEvent,
    append_provenance_event,
    build_file_manifest,
    read_provenance_events,
    resolve_data_uri,
    sha256_file,
    verify_file_manifest,
)


class ProvenanceLogTests(unittest.TestCase):
    """Validate append-only JSONL provenance logs."""

    def test_append_and_read_events_preserves_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "provenance.jsonl"
            append_provenance_event(path, ProvenanceLogEvent("evt1", "create", "2026-06-11T00:00:00Z", {"step": 1}))
            append_provenance_event(path, ProvenanceLogEvent("evt2", "refine", "2026-06-11T00:00:01Z", {"step": 2}))

            events = read_provenance_events(path)

        self.assertEqual([event.event_id for event in events], ["evt1", "evt2"])
        self.assertEqual(events[0].payload, {"step": 1})

    def test_event_requires_non_empty_action(self) -> None:
        with self.assertRaisesRegex(ValueError, "action must be a non-empty string"):
            ProvenanceLogEvent("evt1", "", "2026-06-11T00:00:00Z", {})


class DataUriResolverTests(unittest.TestCase):
    """Validate package-relative and local file URI handling."""

    def test_resolve_package_relative_uri(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            resolved = resolve_data_uri(root, "arrays/profile.bin")

        self.assertEqual(resolved.scheme, "package")
        self.assertEqual(resolved.path.name, "profile.bin")

    def test_resolve_package_uri_scheme(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            resolved = resolve_data_uri(Path(tmpdir), "package://arrays/profile.bin")

        self.assertTrue(resolved.path.as_posix().endswith("/arrays/profile.bin"))

    def test_reject_package_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(ValueError, "escapes package root"):
                resolve_data_uri(Path(tmpdir), "../outside.bin")


class FileManifestTests(unittest.TestCase):
    """Validate deterministic checksums and manifest verification."""

    def test_build_manifest_records_size_and_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "a.txt").write_text("alpha", encoding="utf-8")

            manifest = build_file_manifest(root)

        self.assertEqual(len(manifest), 1)
        self.assertEqual(manifest[0].path, "a.txt")
        self.assertEqual(manifest[0].size_bytes, 5)

    def test_verify_manifest_reports_checksum_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            path = root / "a.txt"
            path.write_text("alpha", encoding="utf-8")
            entry = FileManifestEntry("a.txt", path.stat().st_size, sha256_file(path))
            path.write_text("bravo", encoding="utf-8")

            issues = verify_file_manifest(root, (entry,))

        self.assertEqual(issues[0].code, "checksum_mismatch")

    def test_verify_manifest_reports_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            issues = verify_file_manifest(Path(tmpdir), (FileManifestEntry("missing.txt", 1, "0" * 64),))

        self.assertEqual(issues[0].code, "missing_file")


if __name__ == "__main__":
    unittest.main()
