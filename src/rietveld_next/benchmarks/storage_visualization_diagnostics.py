"""Small deterministic storage, visualization, and diagnostics benchmarks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
import math
from pathlib import Path
import platform
import statistics
import time
from typing import Any

from rietveld_next.benchmarks.results import BenchmarkResult, BenchmarkTiming
from rietveld_next.core.model import Project
from rietveld_next.storage.project_package import read_project_package, write_project_package


@dataclass(frozen=True)
class DecimatedProfile:
    """Profile points selected by bucketed extrema decimation.

    Args:
        x: Decimated x-axis values in original axis units.
        y: Decimated y-axis values in original intensity units.
        original_indices: Zero-based input indices retained in the output.
        preserved_extrema_count: Count of global minimum and maximum y extrema
            present in the decimated output.
    """

    x: tuple[float, ...]
    y: tuple[float, ...]
    original_indices: tuple[int, ...]
    preserved_extrema_count: int


@dataclass(frozen=True)
class ResidualDiagnosticReport:
    """Residual diagnostic tables for benchmark smoke fixtures.

    Args:
        binned_residuals: Per-bin count, mean, and RMS residual summaries.
        outlier_indices: Input indices whose absolute residual exceeds the
            configured sigma threshold.
        bank_summaries: Per-bank count, mean, RMS, minimum, and maximum.
        phase_summaries: Per-phase count, mean, RMS, minimum, and maximum.
        all_finite: Whether every emitted numeric diagnostic is finite.
        checksum: Deterministic checksum over summary values and outlier count.
    """

    binned_residuals: tuple[dict[str, float | int], ...]
    outlier_indices: tuple[int, ...]
    bank_summaries: dict[str, dict[str, float | int]]
    phase_summaries: dict[str, dict[str, float | int]]
    all_finite: bool
    checksum: float

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible diagnostic mapping."""
        return {
            "all_finite": self.all_finite,
            "bank_summaries": {key: dict(value) for key, value in sorted(self.bank_summaries.items())},
            "binned_residuals": [dict(item) for item in self.binned_residuals],
            "checksum": self.checksum,
            "outlier_indices": list(self.outlier_indices),
            "phase_summaries": {key: dict(value) for key, value in sorted(self.phase_summaries.items())},
        }


def run_project_package_storage_benchmark(
    *,
    output_dir: Path,
    point_count: int = 64,
    iterations: int = 1,
    warmup: int = 0,
) -> BenchmarkResult:
    """Benchmark project-package write/read with a JSON profile table payload.

    Args:
        output_dir: Caller-supplied directory where benchmark package files are
            written. The helper does not create hidden temporary locations.
        point_count: Number of deterministic profile-table rows.
        iterations: Number of measured write/read iterations.
        warmup: Number of unmeasured write/read iterations.

    Returns:
        Benchmark result reporting package file sizes, read runtime, write
        runtime, and payload checksum.

    Raises:
        ValueError: If counts are invalid or ``output_dir`` is not a directory.
    """

    _positive_int(point_count, "point_count")
    _positive_int(iterations, "iterations")
    _nonnegative_int(warmup, "warmup")
    root_dir = _existing_directory(output_dir, "output_dir")
    package_root = root_dir / "issue_314_project_package.rnx"
    table_rows = _synthetic_profile_table(point_count)
    project = Project(id="benchmark_project", name="Benchmark Project", experiments=[], phases=[], parameters=[])
    manifest = {
        "format_version": "1.0.0",
        "payloads": [
            {
                "kind": "profile_table",
                "path": "tables/profile_points.json",
                "row_count": point_count,
                "schema": ["x_degree_two_theta", "observed_counts", "calculated_counts"],
                "units": {
                    "x": "degree_two_theta",
                    "observed": "arbitrary_count",
                    "calculated": "arbitrary_count",
                },
            }
        ],
    }

    for _ in range(warmup):
        _write_project_package_fixture(package_root, project, manifest, table_rows)
        _read_project_package_fixture(package_root)

    write_measurements: list[float] = []
    read_measurements: list[float] = []
    checksum = 0.0
    file_sizes: dict[str, int] = {}
    for _ in range(iterations):
        write_start = time.perf_counter()
        _write_project_package_fixture(package_root, project, manifest, table_rows)
        write_measurements.append(time.perf_counter() - write_start)

        read_start = time.perf_counter()
        checksum = _read_project_package_fixture(package_root)
        read_measurements.append(time.perf_counter() - read_start)
        file_sizes = _package_file_sizes(package_root)

    total_measurements = [
        write_seconds + read_seconds
        for write_seconds, read_seconds in zip(write_measurements, read_measurements, strict=True)
    ]
    return BenchmarkResult(
        name="storage_project_package_write_read",
        backend="python",
        status="ok",
        dtype="json",
        input_size=point_count,
        iterations=iterations,
        warmup=warmup,
        checksum=checksum,
        timing=BenchmarkTiming(
            median_seconds=statistics.median(total_measurements),
            min_seconds=min(total_measurements),
            max_seconds=max(total_measurements),
            compile_seconds=None,
        ),
        environment={
            "file_sizes_bytes": file_sizes,
            "issue_numbers": [314],
            "package_root": str(package_root),
            "payload_kinds": ["json_metadata", "profile_table_json"],
            "point_count": point_count,
            "python_version": platform.python_version(),
            "read_max_seconds": max(read_measurements),
            "read_median_seconds": statistics.median(read_measurements),
            "read_min_seconds": min(read_measurements),
            "total_package_bytes": sum(file_sizes.values()),
            "write_max_seconds": max(write_measurements),
            "write_median_seconds": statistics.median(write_measurements),
            "write_min_seconds": min(write_measurements),
        },
    )


def decimate_profile_extrema(
    x: Sequence[float],
    y: Sequence[float],
    *,
    max_points: int,
) -> DecimatedProfile:
    """Downsample profile data by retaining first/last and bucket min/max.

    The algorithm preserves the input order of retained points. For each
    contiguous bucket it keeps the y-minimum and y-maximum rows, then always
    includes the first and last input samples. If ``len(x) <= max_points`` the
    original data is returned unchanged.

    Args:
        x: Monotonic or display-ordered x-axis values.
        y: Intensity values aligned with ``x``.
        max_points: Target upper bound for retained points.

    Returns:
        Decimated profile and a global-extrema preservation count.

    Raises:
        ValueError: If inputs are non-finite, length-mismatched, or too small.
    """

    x_values = _finite_sequence(x, "x")
    y_values = _finite_sequence(y, "y")
    _positive_int(max_points, "max_points")
    if len(x_values) != len(y_values):
        raise ValueError(f"x and y must have the same length, got {len(x_values)} and {len(y_values)}.")
    if len(x_values) < 2:
        raise ValueError("x and y must contain at least two points.")
    if max_points < 4:
        raise ValueError("max_points must be at least 4 for first/last plus min/max decimation.")

    if len(x_values) <= max_points:
        indices = tuple(range(len(x_values)))
    else:
        bucket_count = max(1, (max_points - 2) // 2)
        selected = {0, len(x_values) - 1}
        for start, stop in _bucket_ranges(1, len(x_values) - 1, bucket_count):
            if start >= stop:
                continue
            bucket_indices = range(start, stop)
            min_index = min(bucket_indices, key=lambda index: (y_values[index], index))
            max_index = max(bucket_indices, key=lambda index: (y_values[index], -index))
            selected.add(min_index)
            selected.add(max_index)
        indices = tuple(sorted(selected))

    global_min_index = min(range(len(y_values)), key=lambda index: (y_values[index], index))
    global_max_index = max(range(len(y_values)), key=lambda index: (y_values[index], -index))
    preserved = int(global_min_index in indices) + int(global_max_index in indices)
    return DecimatedProfile(
        x=tuple(x_values[index] for index in indices),
        y=tuple(y_values[index] for index in indices),
        original_indices=indices,
        preserved_extrema_count=preserved,
    )


def run_visualization_decimation_benchmark(
    *,
    point_count: int = 256,
    max_points: int = 64,
    iterations: int = 1,
    warmup: int = 0,
) -> BenchmarkResult:
    """Benchmark deterministic extrema-preserving profile decimation.

    Args:
        point_count: Number of synthetic profile points.
        max_points: Maximum number of retained display points.
        iterations: Number of measured decimation iterations.
        warmup: Number of unmeasured iterations.

    Returns:
        Benchmark result with input size, output size, runtime, and quality
        metrics.
    """

    _positive_int(point_count, "point_count")
    _positive_int(iterations, "iterations")
    _nonnegative_int(warmup, "warmup")
    x_values, y_values = _synthetic_visualization_profile(point_count)
    for _ in range(warmup):
        decimate_profile_extrema(x_values, y_values, max_points=max_points)

    measurements: list[float] = []
    decimated: DecimatedProfile | None = None
    for _ in range(iterations):
        start = time.perf_counter()
        decimated = decimate_profile_extrema(x_values, y_values, max_points=max_points)
        measurements.append(time.perf_counter() - start)
    assert decimated is not None

    checksum = sum(decimated.x) + sum(decimated.y) + float(sum(decimated.original_indices))
    return BenchmarkResult(
        name="visualization_profile_extrema_decimation",
        backend="python",
        status="ok",
        dtype="float64",
        input_size=point_count,
        iterations=iterations,
        warmup=warmup,
        checksum=checksum,
        timing=BenchmarkTiming(
            median_seconds=statistics.median(measurements),
            min_seconds=min(measurements),
            max_seconds=max(measurements),
            compile_seconds=None,
        ),
        environment={
            "algorithm": "bucket_min_max_with_first_last",
            "issue_numbers": [317],
            "input_size": point_count,
            "max_points": max_points,
            "output_size": len(decimated.x),
            "preserved_extrema_count": decimated.preserved_extrema_count,
            "preserved_extrema_possible": 2,
            "python_version": platform.python_version(),
        },
    )


def compute_residual_diagnostics(
    x: Sequence[float],
    residuals: Sequence[float],
    bank_ids: Sequence[str],
    phase_ids: Sequence[str],
    *,
    bin_count: int,
    outlier_sigma: float = 3.0,
) -> ResidualDiagnosticReport:
    """Compute binned residuals, outliers, and bank/phase summaries.

    Args:
        x: Axis values aligned with residuals.
        residuals: Finite residual values.
        bank_ids: Bank label for each residual.
        phase_ids: Phase label for each residual.
        bin_count: Number of contiguous x-order bins.
        outlier_sigma: Absolute residual threshold for outlier detection.

    Returns:
        Deterministic residual diagnostic report.

    Raises:
        ValueError: If input lengths differ or values are invalid.
    """

    x_values = _finite_sequence(x, "x")
    residual_values = _finite_sequence(residuals, "residuals")
    banks = _string_sequence(bank_ids, "bank_ids")
    phases = _string_sequence(phase_ids, "phase_ids")
    _positive_int(bin_count, "bin_count")
    threshold = _positive_float(outlier_sigma, "outlier_sigma")
    expected = len(residual_values)
    if not expected:
        raise ValueError("residuals must contain at least one value.")
    for name, values in (("x", x_values), ("bank_ids", banks), ("phase_ids", phases)):
        if len(values) != expected:
            raise ValueError(f"{name} must have length {expected}, got {len(values)}.")

    binned = tuple(
        _summary_for_values(residual_values[start:stop], extra={"bin_start": start, "bin_stop": stop})
        for start, stop in _bucket_ranges(0, expected, min(bin_count, expected))
    )
    outliers = tuple(index for index, value in enumerate(residual_values) if abs(value) > threshold)
    bank_summaries = _group_summaries(residual_values, banks)
    phase_summaries = _group_summaries(residual_values, phases)
    checksum = (
        sum(float(item["mean"]) + float(item["rms"]) + float(item["count"]) for item in binned)
        + sum(float(item["mean"]) + float(item["rms"]) for item in bank_summaries.values())
        + sum(float(item["mean"]) + float(item["rms"]) for item in phase_summaries.values())
        + float(len(outliers))
    )
    report = ResidualDiagnosticReport(
        binned_residuals=binned,
        outlier_indices=outliers,
        bank_summaries=bank_summaries,
        phase_summaries=phase_summaries,
        all_finite=True,
        checksum=checksum,
    )
    return ResidualDiagnosticReport(
        binned_residuals=report.binned_residuals,
        outlier_indices=report.outlier_indices,
        bank_summaries=report.bank_summaries,
        phase_summaries=report.phase_summaries,
        all_finite=_all_report_numbers_finite(report),
        checksum=report.checksum,
    )


def run_residual_diagnostics_benchmark(
    *,
    point_count: int = 128,
    bin_count: int = 8,
    iterations: int = 1,
    warmup: int = 0,
) -> BenchmarkResult:
    """Benchmark deterministic residual diagnostic computation.

    Args:
        point_count: Number of synthetic residual points.
        bin_count: Number of contiguous bins for residual summaries.
        iterations: Number of measured diagnostic iterations.
        warmup: Number of unmeasured iterations.

    Returns:
        Benchmark result with point counts, bin counts, diagnostics computed,
        finite checks, runtime, and checksum.
    """

    _positive_int(point_count, "point_count")
    _positive_int(iterations, "iterations")
    _nonnegative_int(warmup, "warmup")
    x_values, residuals, banks, phases = _synthetic_residual_fixture(point_count)

    for _ in range(warmup):
        compute_residual_diagnostics(x_values, residuals, banks, phases, bin_count=bin_count)

    measurements: list[float] = []
    report: ResidualDiagnosticReport | None = None
    for _ in range(iterations):
        start = time.perf_counter()
        report = compute_residual_diagnostics(x_values, residuals, banks, phases, bin_count=bin_count)
        measurements.append(time.perf_counter() - start)
    assert report is not None

    return BenchmarkResult(
        name="diagnostics_residual_summary",
        backend="python",
        status="ok",
        dtype="float64",
        input_size=point_count,
        iterations=iterations,
        warmup=warmup,
        checksum=report.checksum,
        timing=BenchmarkTiming(
            median_seconds=statistics.median(measurements),
            min_seconds=min(measurements),
            max_seconds=max(measurements),
            compile_seconds=None,
        ),
        environment={
            "all_diagnostics_finite": report.all_finite,
            "bank_count": len(report.bank_summaries),
            "bin_count": len(report.binned_residuals),
            "diagnostics_computed": [
                "binned_residuals",
                "outlier_detection",
                "bank_summary_statistics",
                "phase_summary_statistics",
            ],
            "issue_numbers": [318],
            "outlier_count": len(report.outlier_indices),
            "phase_count": len(report.phase_summaries),
            "point_count": point_count,
            "python_version": platform.python_version(),
        },
    )


def _write_project_package_fixture(
    package_root: Path,
    project: Project,
    manifest: dict[str, Any],
    table_rows: Sequence[Mapping[str, float]],
) -> None:
    write_project_package(package_root, project, manifest=manifest, overwrite=True)
    table_path = package_root / "tables" / "profile_points.json"
    table_path.parent.mkdir(parents=True, exist_ok=True)
    table_path.write_text(json.dumps(list(table_rows), sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def _read_project_package_fixture(package_root: Path) -> float:
    package = read_project_package(package_root)
    table_path = package.root / "tables" / "profile_points.json"
    rows = json.loads(table_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("profile table payload must be a JSON array.")
    checksum = float(len(package.project.id))
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"profile table row {index} must be a JSON object.")
        checksum += (
            _finite_float(row.get("x_degree_two_theta"), f"row[{index}].x_degree_two_theta")
            + _finite_float(row.get("observed_counts"), f"row[{index}].observed_counts")
            - _finite_float(row.get("calculated_counts"), f"row[{index}].calculated_counts")
        )
    return checksum


def _synthetic_profile_table(point_count: int) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for index in range(point_count):
        x_value = 10.0 + index * 0.05
        observed = 100.0 + float((index % 7) * 3) + 0.25 * index
        calculated = observed - (1.0 if index % 5 == 0 else -0.5)
        rows.append(
            {
                "calculated_counts": calculated,
                "observed_counts": observed,
                "x_degree_two_theta": x_value,
            }
        )
    return rows


def _synthetic_visualization_profile(point_count: int) -> tuple[tuple[float, ...], tuple[float, ...]]:
    x_values = tuple(float(index) for index in range(point_count))
    y_values = tuple(20.0 * math.sin(index / 9.0) + 0.1 * index for index in range(point_count))
    return x_values, y_values


def _synthetic_residual_fixture(
    point_count: int,
) -> tuple[tuple[float, ...], tuple[float, ...], tuple[str, ...], tuple[str, ...]]:
    x_values = tuple(float(index) for index in range(point_count))
    residuals = []
    banks = []
    phases = []
    for index in range(point_count):
        residual = ((index % 9) - 4) / 4.0
        if index == point_count // 2:
            residual = 4.0
        residuals.append(residual)
        banks.append(f"bank_{index % 2}")
        phases.append(f"phase_{index % 3}")
    return x_values, tuple(residuals), tuple(banks), tuple(phases)


def _package_file_sizes(package_root: Path) -> dict[str, int]:
    sizes: dict[str, int] = {}
    for path in sorted(package_root.rglob("*")):
        if path.is_file():
            sizes[str(path.relative_to(package_root))] = path.stat().st_size
    return sizes


def _bucket_ranges(start: int, stop: int, bucket_count: int) -> tuple[tuple[int, int], ...]:
    _positive_int(bucket_count, "bucket_count")
    if start > stop:
        raise ValueError("bucket start must be less than or equal to stop.")
    span = stop - start
    if span == 0:
        return ()
    ranges: list[tuple[int, int]] = []
    for bucket_index in range(bucket_count):
        bucket_start = start + (span * bucket_index) // bucket_count
        bucket_stop = start + (span * (bucket_index + 1)) // bucket_count
        if bucket_start < bucket_stop:
            ranges.append((bucket_start, bucket_stop))
    return tuple(ranges)


def _group_summaries(values: Sequence[float], labels: Sequence[str]) -> dict[str, dict[str, float | int]]:
    grouped: dict[str, list[float]] = {}
    for value, label in zip(values, labels, strict=True):
        grouped.setdefault(label, []).append(value)
    return {
        label: _summary_for_values(group_values)
        for label, group_values in sorted(grouped.items())
    }


def _summary_for_values(
    values: Sequence[float],
    *,
    extra: Mapping[str, int] | None = None,
) -> dict[str, float | int]:
    if not values:
        raise ValueError("summary values must contain at least one value.")
    mean = sum(values) / float(len(values))
    rms = math.sqrt(sum(value * value for value in values) / float(len(values)))
    summary: dict[str, float | int] = {
        "count": len(values),
        "max": max(values),
        "mean": mean,
        "min": min(values),
        "rms": rms,
    }
    if extra is not None:
        summary.update(dict(extra))
    return summary


def _all_report_numbers_finite(report: ResidualDiagnosticReport) -> bool:
    return _json_numbers_finite(report.to_dict())


def _json_numbers_finite(value: Any) -> bool:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return True
    if isinstance(value, int | float):
        return math.isfinite(float(value))
    if isinstance(value, list | tuple):
        return all(_json_numbers_finite(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _json_numbers_finite(item) for key, item in value.items())
    return False


def _existing_directory(path: Path, name: str) -> Path:
    resolved = Path(path)
    if not resolved.exists() or not resolved.is_dir():
        raise ValueError(f"{name} must be an existing directory, got {resolved}.")
    return resolved


def _finite_sequence(values: Sequence[float], name: str) -> tuple[float, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    return tuple(_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values))


def _string_sequence(values: Sequence[str], name: str) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of non-empty strings.")
    labels = tuple(values)
    for index, label in enumerate(labels):
        if not isinstance(label, str) or not label:
            raise ValueError(f"{name}[{index}] must be a non-empty string.")
    return labels


def _finite_float(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _positive_float(value: float, name: str) -> float:
    number = _finite_float(value, name)
    if number <= 0.0:
        raise ValueError(f"{name} must be positive, got {number!r}.")
    return number


def _positive_int(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value!r}.")


def _nonnegative_int(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer, got {value!r}.")
