"""Tests for storage interchange adapters and CLI helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rietveld_next.core.model import ParameterPath, Project, RefinementParameter
from rietveld_next.storage import (
    export_arrow_parameter_table,
    hdf5_metadata_reference,
    nexus_file_reference,
    storage_cli_main,
    validate_project_schema_file,
    write_parquet_result_table,
    zarr_profile_array_reference,
)


class StorageExchangeTests(unittest.TestCase):
    """Validate deterministic adapter metadata and placeholder exports."""

    def test_external_dataset_references_are_json_compatible(self) -> None:
        nexus = nexus_file_reference("package://data/file.nxs", "/entry/data/y", shape=(2, 3), dtype="float64")
        hdf5 = hdf5_metadata_reference("package://data/file.h5", "/metadata/wavelength", units="angstrom")
        zarr = zarr_profile_array_reference("package://arrays/profile.zarr", "/profile/intensity")

        self.assertEqual(nexus.to_dict()["format"], "nexus")
        self.assertEqual(hdf5.to_dict()["units"], "angstrom")
        self.assertEqual(zarr.to_dict()["dataset_path"], "/profile/intensity")

    def test_external_dataset_reference_rejects_relative_internal_path(self) -> None:
        with self.assertRaisesRegex(ValueError, "absolute internal path"):
            nexus_file_reference("package://data/file.nxs", "entry/data")

    def test_parquet_and_arrow_placeholder_writers_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parquet_path = write_parquet_result_table(root / "results.parquet", ({"b": 2, "a": 1},))
            arrow_path = export_arrow_parameter_table(
                root / "parameters.arrow",
                (
                    RefinementParameter(
                        id="p1",
                        path=ParameterPath("phase", "phase1", ("cell", "a")),
                        value=5.0,
                        refine=True,
                    ),
                ),
            )

            self.assertEqual(parquet_path.read_text(encoding="utf-8"), '{"a":1,"b":2}\n')
            self.assertIn('"path":"phase/phase1/cell/a"', arrow_path.read_text(encoding="utf-8"))


class StorageCliTests(unittest.TestCase):
    """Validate schema validation CLI helpers."""

    def test_validate_project_schema_file_reports_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "project.json"
            path.write_text(Project(id="project1", experiments=[], phases=[], parameters=[]).to_json(), encoding="utf-8")

            ok, message = validate_project_schema_file(path)

        self.assertTrue(ok)
        self.assertEqual(message, "ok")

    def test_validate_project_schema_file_reports_schema_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "project.json"
            path.write_text('{"id":"project1"}', encoding="utf-8")

            ok, message = validate_project_schema_file(path)

        self.assertFalse(ok)
        self.assertTrue(message.startswith("schema_error:"))

    def test_storage_cli_validate_project_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "project.json"
            path.write_text(Project(id="project1", experiments=[], phases=[], parameters=[]).to_json(), encoding="utf-8")

            exit_code = storage_cli_main(["validate-project", str(path)])

        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
