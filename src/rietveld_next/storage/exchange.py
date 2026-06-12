"""Dependency-free storage interchange adapter records.

These helpers describe NeXus/HDF5/Zarr/Parquet/Arrow interchange targets
without importing optional binary storage libraries. They provide deterministic
metadata and placeholder text exports for early workflow plumbing.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Literal

from rietveld_next.core.model import RefinementParameter


@dataclass(frozen=True)
class ExternalDatasetReference:
    """Reference to an external array dataset.

    Args:
        uri: File URI or package-relative URI.
        dataset_path: Internal path such as a NeXus/HDF5 dataset path or a Zarr
            array key.
        format: Storage family label.
        shape: Optional array shape.
        dtype: Optional dtype label.
        units: Optional physical units.
    """

    uri: str
    dataset_path: str
    format: Literal["nexus", "hdf5", "zarr"]
    shape: tuple[int, ...] = ()
    dtype: str | None = None
    units: str | None = None

    def __post_init__(self) -> None:
        """Validate external dataset metadata."""
        if not self.uri:
            raise ValueError("uri must be non-empty.")
        if not self.dataset_path.startswith("/"):
            raise ValueError("dataset_path must be an absolute internal path.")
        for dimension in self.shape:
            if not isinstance(dimension, int) or dimension <= 0:
                raise ValueError("shape dimensions must be positive integers.")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible reference mapping."""
        data: dict[str, Any] = {
            "dataset_path": self.dataset_path,
            "format": self.format,
            "shape": list(self.shape),
            "uri": self.uri,
        }
        if self.dtype is not None:
            data["dtype"] = self.dtype
        if self.units is not None:
            data["units"] = self.units
        return data


def nexus_file_reference(uri: str, dataset_path: str, **metadata: Any) -> ExternalDatasetReference:
    """Create a NeXus dataset reference."""
    return ExternalDatasetReference(uri=uri, dataset_path=dataset_path, format="nexus", **metadata)


def hdf5_metadata_reference(uri: str, dataset_path: str, **metadata: Any) -> ExternalDatasetReference:
    """Create an HDF5 metadata dataset reference."""
    return ExternalDatasetReference(uri=uri, dataset_path=dataset_path, format="hdf5", **metadata)


def zarr_profile_array_reference(uri: str, dataset_path: str, **metadata: Any) -> ExternalDatasetReference:
    """Create a Zarr profile-array reference."""
    return ExternalDatasetReference(uri=uri, dataset_path=dataset_path, format="zarr", **metadata)


def write_parquet_result_table(path: Path, rows: tuple[dict[str, Any], ...]) -> Path:
    """Write a deterministic JSON-lines placeholder for a result table.

    The file extension may be ``.parquet`` for workflow compatibility, but the
    contents are UTF-8 JSON lines until an optional Parquet dependency is added.
    """
    return _write_jsonl_table(path, rows)


def export_arrow_parameter_table(path: Path, parameters: tuple[RefinementParameter, ...]) -> Path:
    """Write a deterministic JSON-lines placeholder for Arrow parameter data."""
    rows = tuple(
        {
            "id": parameter.id,
            "path": str(parameter.path),
            "refine": parameter.refine,
            "value": parameter.value,
        }
        for parameter in parameters
    )
    return _write_jsonl_table(path, rows)


def _write_jsonl_table(path: Path, rows: tuple[dict[str, Any], ...]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("table rows must be dictionaries.")
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return target
