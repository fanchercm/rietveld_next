"""Lightweight synthetic EDXRD benchmark workflow for high-pressure fixtures."""

from __future__ import annotations

import json
from pathlib import Path
import platform
import statistics
import time
from collections.abc import Sequence
from typing import Any

from rietveld_next.benchmarks.results import BenchmarkResult, BenchmarkTiming, validate_benchmark_result_dict
from rietveld_next.edxrd.axis import EnergyHistogramAxis
from rietveld_next.edxrd.bragg import fixed_angle_bragg_energy_keV
from rietveld_next.edxrd.diagnostics import compute_edxrd_residual_diagnostics
from rietveld_next.edxrd.high_pressure import (
    BirchMurnaghanEquationOfState,
    EquationOfStateHook,
    HighPressureMarker,
)
from rietveld_next.edxrd.response import (
    DetectorResponseModel,
    EDXRDResponsePeak,
    GaussianDetectorResponse,
)


def run_edxrd_synthetic_benchmark(
    *,
    channel_count: int = 64,
    iterations: int = 1,
    warmup: int = 0,
) -> BenchmarkResult:
    """Run a small deterministic EDXRD high-pressure benchmark.

    Args:
        channel_count: Number of energy bins. Must be positive.
        iterations: Number of measured iterations. Must be positive.
        warmup: Number of unmeasured warmup iterations. Must be non-negative.

    Returns:
        Benchmark result with reproducibility metadata and residual
        diagnostics from a synthetic high-pressure EDXRD fixture.

    Raises:
        ValueError: If sizing inputs are invalid.
    """

    _positive_int(channel_count, "channel_count")
    _positive_int(iterations, "iterations")
    _non_negative_int(warmup, "warmup")
    fixture = _build_fixture(channel_count)

    for _ in range(warmup):
        _evaluate_fixture(fixture)

    timings: list[float] = []
    output: dict[str, Any] | None = None
    for _ in range(iterations):
        start = time.perf_counter()
        output = _evaluate_fixture(fixture)
        timings.append(time.perf_counter() - start)

    if output is None:
        raise ValueError("benchmark did not produce output.")
    environment = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "device": "cpu",
        "issue_numbers": [161, 162, 163, 165, 167],
        "axis": fixture["axis"].to_dict(),
        "marker": fixture["marker"].to_project_entity(),
        "eos": fixture["eos_hook"].eos.to_dict(),
        "two_theta_degrees": fixture["two_theta_degrees"],
        "diagnostics": output["diagnostics"],
        "peak_energies_keV": output["peak_energies_keV"],
        "assumptions": {
            "validation_status": "synthetic fixture only; not cross-software scientific validation",
            "compression_model": "third-order Birch-Murnaghan EOS with isotropic d-spacing scaling",
            "residual_convention": "observed - calculated",
            "randomness": "none",
        },
    }
    return BenchmarkResult(
        name="edxrd_high_pressure_synthetic",
        backend="python",
        status="ok",
        dtype="float64",
        input_size=channel_count,
        iterations=iterations,
        warmup=warmup,
        checksum=output["checksum"],
        timing=BenchmarkTiming(
            median_seconds=statistics.median(timings),
            min_seconds=min(timings),
            max_seconds=max(timings),
            compile_seconds=None,
        ),
        environment=environment,
    )


def write_edxrd_synthetic_benchmark_result(
    output_path: str | Path,
    *,
    channel_count: int = 64,
    iterations: int = 1,
    warmup: int = 0,
) -> BenchmarkResult:
    """Run the synthetic benchmark and write reproducible JSON output.

    Args:
        output_path: Destination JSON file path.
        channel_count: Number of energy bins.
        iterations: Number of measured iterations.
        warmup: Number of unmeasured warmup iterations.

    Returns:
        The benchmark result that was written.

    Raises:
        ValueError: If the path or benchmark inputs are invalid.
        OSError: If the destination cannot be written.
    """

    path = _output_path(output_path)
    result = run_edxrd_synthetic_benchmark(
        channel_count=channel_count,
        iterations=iterations,
        warmup=warmup,
    )
    payload = result.to_dict()
    validate_benchmark_result_dict(payload)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _build_fixture(channel_count: int) -> dict[str, Any]:
    axis = EnergyHistogramAxis.from_linear_calibration(
        channel_count=channel_count,
        offset_keV=24.0,
        gain_keV_per_channel=0.18,
    )
    marker = HighPressureMarker(
        "m28-synthetic",
        pressure_gpa=8.0,
        pressure_uncertainty_gpa=0.1,
        pressure_standard="synthetic ruby scale",
        calibrant="synthetic cubic standard",
        provenance={"fixture": "M28 synthetic high-pressure EDXRD"},
    )
    eos = BirchMurnaghanEquationOfState(
        reference_volume_angstrom3=64.0,
        bulk_modulus_gpa=180.0,
        bulk_modulus_derivative=4.0,
    )
    eos_hook = EquationOfStateHook(
        eos=eos,
        reference_d_spacings_angstrom=(3.50, 3.05, 2.72),
        labels=("111", "200", "220"),
    )
    return {
        "axis": axis,
        "marker": marker,
        "eos_hook": eos_hook,
        "two_theta_degrees": 8.0,
    }


def _evaluate_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    axis = fixture["axis"]
    marker = fixture["marker"]
    eos_hook = fixture["eos_hook"]
    two_theta_degrees = fixture["two_theta_degrees"]
    d_spacings = eos_hook.compressed_d_spacings_angstrom(marker)
    peak_energies = tuple(
        fixed_angle_bragg_energy_keV(d_spacing, two_theta_degrees)
        for d_spacing in d_spacings
    )
    peaks = tuple(
        EDXRDResponsePeak(
            energy_keV=energy,
            area_counts=150.0 + 25.0 * index,
            label=eos_hook.labels[index],
        )
        for index, energy in enumerate(peak_energies)
    )
    model = DetectorResponseModel(
        gaussian=GaussianDetectorResponse(fwhm_keV=0.28),
        provenance={"benchmark": "M28 high-pressure synthetic"},
    )
    calculated = model.evaluate(axis, peaks).bin_counts
    observed = tuple(max(0.0, value + _deterministic_residual(index)) for index, value in enumerate(calculated))
    uncertainties = tuple(max(1.0, value**0.5) for value in observed)
    diagnostics = compute_edxrd_residual_diagnostics(
        axis,
        observed,
        calculated,
        uncertainties_counts=uncertainties,
        fitted_parameter_count=3,
        provenance={"source": "M28 synthetic benchmark fixture"},
    )
    checksum = _weighted_checksum(observed) + _weighted_checksum(diagnostics.weighted_residuals)
    return {
        "checksum": checksum,
        "diagnostics": diagnostics.to_dict(),
        "peak_energies_keV": list(peak_energies),
    }


def _deterministic_residual(index: int) -> float:
    pattern = (-0.75, 0.25, 0.5, -0.25)
    return pattern[index % len(pattern)]


def _weighted_checksum(values: Sequence[float]) -> float:
    return sum((index + 1) * float(value) for index, value in enumerate(values))


def _output_path(value: str | Path) -> Path:
    if isinstance(value, str):
        if not value.strip():
            raise ValueError("output_path must be non-empty.")
        return Path(value)
    if isinstance(value, Path):
        return value
    raise ValueError("output_path must be a string or pathlib.Path.")


def _positive_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return value


def _non_negative_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer.")
    return value
