"""Tests for architecture foundation primitives."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from rietveld_next.core.architecture import (
    ApiStability,
    ArchitectureError,
    ArchitectureErrorCode,
    FeatureFlag,
    FeatureFlagRegistry,
    build_release_manifest,
    capture_environment,
    create_provenance_event,
    load_configuration,
)


class ArchitectureFoundationTests(unittest.TestCase):
    """Validate deterministic M01 architecture foundation helpers."""

    def test_load_configuration_merges_defaults_files_and_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "engine": {"threads": 4},
                        "feature": {"enabled": False},
                    }
                ),
                encoding="utf-8",
            )

            config = load_configuration(
                [path],
                defaults={"engine": {"threads": 1, "backend": "python"}, "schema_version": "1.0.0"},
                overrides={"feature": {"enabled": True}},
            )

        self.assertEqual(
            config,
            {
                "engine": {"backend": "python", "threads": 4},
                "feature": {"enabled": True},
                "schema_version": "1.0.0",
            },
        )

    def test_load_configuration_rejects_invalid_json_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.json"
            path.write_text("[1, 2, 3]", encoding="utf-8")

            with self.assertRaises(ArchitectureError) as context:
                load_configuration([path])

        self.assertEqual(context.exception.code, ArchitectureErrorCode.INVALID_CONFIGURATION)
        self.assertEqual(context.exception.path, str(path))

    def test_feature_flag_registry_resolves_overrides(self) -> None:
        registry = FeatureFlagRegistry(
            (
                FeatureFlag(
                    name="profile.kernel.v2",
                    description="Enable the second profile-kernel interface.",
                    default_enabled=False,
                    stability=ApiStability.PROVISIONAL,
                    owner="diffraction",
                ),
            )
        )

        self.assertFalse(registry.is_enabled("profile.kernel.v2"))
        self.assertTrue(registry.is_enabled("profile.kernel.v2", {"profile.kernel.v2": True}))
        self.assertEqual(registry.to_dict()["flags"][0]["stability"], "provisional")

    def test_duplicate_feature_flags_are_rejected(self) -> None:
        flag = FeatureFlag(name="duplicate.flag", description="Duplicate test flag.")

        with self.assertRaises(ArchitectureError) as context:
            FeatureFlagRegistry((flag, flag))

        self.assertEqual(context.exception.code, ArchitectureErrorCode.INVALID_FEATURE_FLAG)
        self.assertEqual(context.exception.details["duplicates"], ["duplicate.flag"])

    def test_create_provenance_event_derives_stable_id(self) -> None:
        first = create_provenance_event(
            actor="codex",
            action="m01.foundation.updated",
            timestamp_utc="2026-06-11T12:00:00Z",
            subject="src/rietveld_next/core/architecture/foundation.py",
            details={"issues": [4, 7, 8, 9, 11, 12, 15]},
        )
        second = create_provenance_event(
            actor="codex",
            action="m01.foundation.updated",
            timestamp_utc="2026-06-11T12:00:00Z",
            subject="src/rietveld_next/core/architecture/foundation.py",
            details={"issues": [4, 7, 8, 9, 11, 12, 15]},
        )

        self.assertEqual(first.event_id, second.event_id)
        self.assertTrue(first.event_id.startswith("evt_"))
        self.assertEqual(first.to_dict()["schema_version"], "1.0.0")

    def test_provenance_event_details_are_immutable_after_id_derivation(self) -> None:
        event = create_provenance_event(
            actor="codex",
            action="m01.foundation.updated",
            timestamp_utc="2026-06-11T12:00:00Z",
            details={"nested": {"issues": [4, 8]}},
        )
        before = event.to_dict()

        with self.assertRaises(TypeError):
            event.details["extra"] = "mutation"  # type: ignore[index]
        with self.assertRaises(TypeError):
            event.details["nested"]["issues"] += (9,)  # type: ignore[index,operator]

        self.assertEqual(event.to_dict(), before)

    def test_invalid_provenance_timestamp_is_rejected(self) -> None:
        with self.assertRaises(ArchitectureError) as context:
            create_provenance_event(actor="codex", action="bad.timestamp", timestamp_utc="2026-06-11")

        self.assertEqual(context.exception.code, ArchitectureErrorCode.INVALID_PROVENANCE_EVENT)

    def test_capture_environment_includes_only_requested_variables(self) -> None:
        old_selected = os.environ.get("RIETVELD_NEXT_TEST_ENV")
        old_omitted = os.environ.get("RIETVELD_NEXT_OMITTED_ENV")
        os.environ["RIETVELD_NEXT_TEST_ENV"] = "selected"
        os.environ["RIETVELD_NEXT_OMITTED_ENV"] = "omitted"
        try:
            snapshot = capture_environment(["RIETVELD_NEXT_TEST_ENV"])
        finally:
            _restore_env("RIETVELD_NEXT_TEST_ENV", old_selected)
            _restore_env("RIETVELD_NEXT_OMITTED_ENV", old_omitted)

        data = snapshot.to_dict()
        self.assertEqual(data["environment_variables"], {"RIETVELD_NEXT_TEST_ENV": "selected"})
        self.assertIn("python_version", data)
        self.assertIn("platform", data)

    def test_build_release_manifest_hashes_artifacts_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            artifact = root / "dist" / "artifact.txt"
            artifact.parent.mkdir()
            artifact.write_text("release payload\n", encoding="utf-8")

            manifest = build_release_manifest(
                root=root,
                artifact_paths=[artifact],
                version="0.1.0",
                created_at_utc="2026-06-11T12:00:00Z",
            )

        artifact_data = manifest.to_dict()["artifacts"][0]
        self.assertEqual(artifact_data["path"], "dist/artifact.txt")
        self.assertEqual(artifact_data["sha256"], hashlib.sha256(b"release payload\n").hexdigest())
        self.assertEqual(artifact_data["size_bytes"], 16)

    def test_build_release_manifest_rejects_missing_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ArchitectureError) as context:
                build_release_manifest(
                    root=Path(tmpdir),
                    artifact_paths=[Path(tmpdir) / "missing.txt"],
                    version="0.1.0",
                    created_at_utc="2026-06-11T12:00:00Z",
                )

        self.assertEqual(context.exception.code, ArchitectureErrorCode.INVALID_ARTIFACT)


def _restore_env(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


if __name__ == "__main__":
    unittest.main()
