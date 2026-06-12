"""Small deterministic physics proxy benchmarks.

These helpers are opt-in smoke workloads for benchmark plumbing. They exercise
existing TOF, neutron, magnetic, EDXRD, and diffraction helper APIs with
synthetic fixtures, but they are not scientific validation calculations.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
import math
from pathlib import Path
import platform
import statistics
import time
from typing import Any

from rietveld_next.benchmarks.results import BenchmarkResult, BenchmarkTiming
from rietveld_next.diffraction.profiles import gaussian_profile
from rietveld_next.edxrd.axis import EnergyHistogramAxis
from rietveld_next.edxrd.bragg import fixed_angle_bragg_energy_keV
from rietveld_next.neutron.magnetic.moment import MagneticMoment
from rietveld_next.neutron.magnetic.propagation import PropagationVector
from rietveld_next.neutron.scattering_lengths import lookup_bound_coherent_scattering_length
from rietveld_next.tof.axis import TimeOfFlightHistogramAxis
from rietveld_next.tof.bank import TimeOfFlightDetectorBank
from rietveld_next.tof.calibration import TimeOfFlightCalibrationParameters


_ASSUMPTIONS = {
    "validation_status": "synthetic proxy only; not a scientific validation result",
    "randomness": "none; fixtures are deterministic and seed-free",
    "default_cost": "small smoke workload suitable for normal unit tests",
}


def run_multi_bank_tof_profile_proxy_benchmark(
    *,
    bank_count: int = 2,
    bins_per_bank: int = 64,
    reflection_count: int = 3,
    iterations: int = 1,
    warmup: int = 0,
) -> BenchmarkResult:
    """Benchmark a synthetic multi-bank TOF profile proxy.

    The proxy evaluates Gaussian profile peaks on bank-specific TOF axes. Peak
    centers use the conventional ``TOF = DIFA*d^2 + DIFC*d + zero`` calibration
    expression with d-spacing in angstroms and TOF in microseconds.

    Args:
        bank_count: Number of synthetic detector banks. Must be at least two.
        bins_per_bank: Number of TOF bins per bank. Must be positive.
        reflection_count: Number of synthetic d-spacing peaks. Must be
            positive.
        iterations: Measured steady-state iterations. Must be positive.
        warmup: Unmeasured warmup iterations. Must be non-negative.

    Returns:
        Machine-readable benchmark result with per-bank checksum metadata.

    Raises:
        ValueError: If sizing inputs are invalid.
    """

    _minimum_int(bank_count, "bank_count", minimum=2)
    _positive_int(bins_per_bank, "bins_per_bank")
    _positive_int(reflection_count, "reflection_count")
    _positive_int(iterations, "iterations")
    _nonnegative_int(warmup, "warmup")

    fixture = _build_tof_fixture(bank_count, bins_per_bank, reflection_count)
    return _time_benchmark(
        name="multi_bank_tof_profile_proxy",
        input_size=bank_count * bins_per_bank,
        iterations=iterations,
        warmup=warmup,
        workload=lambda: _evaluate_tof_fixture(fixture),
        environment={
            "issue_numbers": [308],
            "bank_count": bank_count,
            "bins_per_bank": bins_per_bank,
            "reflection_count": reflection_count,
            "axis_units": "microsecond",
            "calibration_expression": "tof_microseconds = difa*d_spacing^2 + difc*d_spacing + zero",
            "calibration_units": {
                "d_spacing": "angstrom",
                "difc": "microsecond/angstrom",
                "difa": "microsecond/angstrom^2",
                "zero": "microsecond",
            },
            "assumptions": dict(_ASSUMPTIONS),
        },
        environment_from_output=lambda output: {
            "banks": output["banks"],
            "aggregate_intensity_checksum": output["checksum"],
        },
    )


def run_neutron_scattering_lookup_proxy_benchmark(
    *,
    lookup_count: int = 64,
    iterations: int = 1,
    warmup: int = 0,
    use_cached_keys: bool = False,
) -> BenchmarkResult:
    """Benchmark repeated neutron bound coherent scattering-length lookups.

    Args:
        lookup_count: Number of isotope labels looked up per iteration. Must
            be positive.
        iterations: Measured steady-state iterations. Must be positive.
        warmup: Unmeasured warmup iterations. Must be non-negative.
        use_cached_keys: If true, benchmark repeated access to pre-normalized
            lookup-table keys. If false, include alias normalization work.

    Returns:
        Machine-readable benchmark result with lookup metadata.

    Raises:
        ValueError: If sizing inputs are invalid.
    """

    _positive_int(lookup_count, "lookup_count")
    _positive_int(iterations, "iterations")
    _nonnegative_int(warmup, "warmup")
    if not isinstance(use_cached_keys, bool):
        raise ValueError(f"use_cached_keys must be a boolean, got {use_cached_keys!r}.")

    labels = _scattering_lookup_labels(lookup_count, use_cached_keys=use_cached_keys)
    variant = "cached_keys" if use_cached_keys else "alias_normalization"
    return _time_benchmark(
        name=f"neutron_scattering_length_lookup_proxy_{variant}",
        input_size=lookup_count,
        iterations=iterations,
        warmup=warmup,
        workload=lambda: _evaluate_scattering_lookup(labels),
        environment={
            "issue_numbers": [310],
            "lookup_count": lookup_count,
            "variant": variant,
            "value_units": "femtometer",
            "known_values": {
                "1H_bound_coherent_fm": lookup_bound_coherent_scattering_length("1H").bound_coherent_fm,
                "2H_bound_coherent_fm": lookup_bound_coherent_scattering_length("2H").bound_coherent_fm,
                "nat_C_bound_coherent_fm": lookup_bound_coherent_scattering_length("nat C").bound_coherent_fm,
            },
            "assumptions": dict(_ASSUMPTIONS),
        },
        environment_from_output=lambda output: {
            "unique_result_isotopes": output["unique_result_isotopes"],
            "source": output["source"],
        },
    )


def run_magnetic_structure_factor_proxy_benchmark(
    *,
    reflection_count: int = 8,
    iterations: int = 1,
    warmup: int = 0,
) -> BenchmarkResult:
    """Benchmark a simplified magnetic structure-factor proxy.

    The proxy sums transverse magnetic moment magnitudes with phase factors for
    deterministic synthetic sites and reflections. It omits magnetic form
    factors, symmetry, polarization factors beyond the simple transverse
    projection, absorption, extinction, and instrument corrections.

    Args:
        reflection_count: Number of synthetic magnetic reflections. Must be
            positive.
        iterations: Measured steady-state iterations. Must be positive.
        warmup: Unmeasured warmup iterations. Must be non-negative.

    Returns:
        Machine-readable benchmark result with reflection and checksum
        metadata.

    Raises:
        ValueError: If sizing inputs are invalid.
    """

    _positive_int(reflection_count, "reflection_count")
    _positive_int(iterations, "iterations")
    _nonnegative_int(warmup, "warmup")

    fixture = _build_magnetic_fixture(reflection_count)
    return _time_benchmark(
        name="magnetic_structure_factor_proxy",
        input_size=reflection_count,
        iterations=iterations,
        warmup=warmup,
        workload=lambda: _evaluate_magnetic_fixture(fixture),
        environment={
            "issue_numbers": [311],
            "reflection_count": reflection_count,
            "moment_units": "bohr_magneton",
            "phase_units": "radian",
            "assumptions": {
                **_ASSUMPTIONS,
                "magnetic_model": (
                    "transverse moment phase-sum proxy only; not a full magnetic "
                    "structure-factor calculation"
                ),
            },
        },
        environment_from_output=lambda output: {
            "reflection_checksums": output["reflection_checksums"],
            "propagation_vector": output["propagation_vector"],
        },
    )


def run_edxrd_detector_response_proxy_benchmark(
    *,
    channel_count: int = 64,
    peak_count: int = 3,
    iterations: int = 1,
    warmup: int = 0,
    include_tail: bool = False,
) -> BenchmarkResult:
    """Benchmark a synthetic EDXRD detector-response proxy.

    The proxy evaluates Gaussian responses on an energy histogram axis. When
    ``include_tail`` is true, it adds a deterministic high-energy exponential
    tail component to each peak.

    Args:
        channel_count: Number of detector energy channels. Must be positive.
        peak_count: Number of synthetic Bragg energy peaks. Must be positive.
        iterations: Measured steady-state iterations. Must be positive.
        warmup: Unmeasured warmup iterations. Must be non-negative.
        include_tail: Include a one-sided exponential tail proxy.

    Returns:
        Machine-readable benchmark result with detector-response metadata.

    Raises:
        ValueError: If sizing inputs are invalid.
    """

    _positive_int(channel_count, "channel_count")
    _positive_int(peak_count, "peak_count")
    _positive_int(iterations, "iterations")
    _nonnegative_int(warmup, "warmup")
    if not isinstance(include_tail, bool):
        raise ValueError(f"include_tail must be a boolean, got {include_tail!r}.")

    fixture = _build_edxrd_fixture(channel_count, peak_count, include_tail=include_tail)
    variant = "gaussian_with_tail" if include_tail else "gaussian"
    return _time_benchmark(
        name=f"edxrd_detector_response_proxy_{variant}",
        input_size=channel_count,
        iterations=iterations,
        warmup=warmup,
        workload=lambda: _evaluate_edxrd_fixture(fixture),
        environment={
            "issue_numbers": [312],
            "channel_count": channel_count,
            "peak_count": peak_count,
            "detector_response_variant": variant,
            "axis_units": "keV",
            "calibration_metadata": fixture["axis"].to_dict(),
            "bragg_two_theta_degrees": fixture["two_theta_degrees"],
            "assumptions": {
                **_ASSUMPTIONS,
                "detector_response": (
                    "Gaussian energy response with optional synthetic tail; "
                    "not calibrated to a physical detector"
                ),
            },
        },
        environment_from_output=lambda output: {
            "finite_output": output["finite_output"],
            "response_sample_count": output["response_sample_count"],
            "peak_energies_keV": output["peak_energies_keV"],
        },
    )


def _time_benchmark(
    *,
    name: str,
    input_size: int,
    iterations: int,
    warmup: int,
    workload: Callable[[], dict[str, Any]],
    environment: dict[str, Any],
    environment_from_output: Callable[[dict[str, Any]], dict[str, Any]],
) -> BenchmarkResult:
    for _ in range(warmup):
        workload()

    measurements: list[float] = []
    output: dict[str, Any] | None = None
    for _ in range(iterations):
        start = time.perf_counter()
        output = workload()
        measurements.append(time.perf_counter() - start)

    if output is None:
        raise ValueError("workload did not produce output.")

    full_environment = _base_environment()
    full_environment.update(environment)
    full_environment.update(environment_from_output(output))
    return BenchmarkResult(
        name=name,
        backend="python",
        status="ok",
        dtype="float64",
        input_size=input_size,
        iterations=iterations,
        warmup=warmup,
        checksum=float(output["checksum"]),
        timing=BenchmarkTiming(
            median_seconds=statistics.median(measurements),
            min_seconds=min(measurements),
            max_seconds=max(measurements),
            compile_seconds=None,
        ),
        environment=full_environment,
    )


def _build_tof_fixture(bank_count: int, bins_per_bank: int, reflection_count: int) -> dict[str, Any]:
    d_spacings = tuple(0.75 + 0.35 * index for index in range(reflection_count))
    banks = []
    for index in range(bank_count):
        bank_id = f"bank-{index + 1}"
        calibration = TimeOfFlightCalibrationParameters(
            difc_microseconds_per_angstrom=9000.0 + 450.0 * index,
            difa_microseconds_per_angstrom_squared=(-2.0) ** index,
            zero_microseconds=6.0 + 1.5 * index,
            bank_id=bank_id,
            d_spacing_range_angstrom=(min(d_spacings), max(d_spacings)),
            source="synthetic benchmark proxy",
        )
        bank = TimeOfFlightDetectorBank(
            bank_id,
            two_theta_degrees=90.0 + 12.5 * index,
            detector_count=64 + 8 * index,
            calibration=calibration,
        )
        first_center = calibration.difc_microseconds_per_angstrom * 0.65
        width = 55.0 + 3.0 * index
        centers = tuple(first_center + width * sample for sample in range(bins_per_bank))
        axis = TimeOfFlightHistogramAxis.from_centers(
            centers,
            bin_width_microseconds=width,
            bank_id=bank_id,
        )
        banks.append({"bank": bank, "axis": axis})
    return {"banks": tuple(banks), "d_spacings": d_spacings}


def _evaluate_tof_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    aggregate_checksum = 0.0
    bank_reports = []
    for bank_index, bank_payload in enumerate(fixture["banks"]):
        bank = bank_payload["bank"]
        axis = bank_payload["axis"]
        profile = [0.0 for _ in axis.centers_microseconds]
        peak_centers = []
        bank_start = time.perf_counter()
        for reflection_index, d_spacing in enumerate(fixture["d_spacings"]):
            center = _tof_center_microseconds(bank.calibration, d_spacing)
            peak_centers.append(center)
            area = (reflection_index + 1) * bank.detector_count * 0.25
            fwhm = 70.0 + 5.0 * bank_index + 4.0 * reflection_index
            contribution = gaussian_profile(
                axis.centers_microseconds,
                center=center,
                fwhm=fwhm,
                area=area,
            )
            profile = [left + right for left, right in zip(profile, contribution, strict=True)]

        bank_checksum = _weighted_checksum(profile)
        bank_runtime_seconds = time.perf_counter() - bank_start
        aggregate_checksum += (bank_index + 1) * bank_checksum
        bank_reports.append(
            {
                "bank_id": bank.bank_id,
                "bin_count": axis.bin_count,
                "detector_count": bank.detector_count,
                "calibration": bank.calibration.to_dict(),
                "peak_centers_microseconds": peak_centers,
                "checksum": bank_checksum,
                "runtime_seconds": bank_runtime_seconds,
            }
        )
    return {"checksum": aggregate_checksum, "banks": bank_reports}


def _tof_center_microseconds(
    calibration: TimeOfFlightCalibrationParameters,
    d_spacing_angstrom: float,
) -> float:
    return (
        calibration.difa_microseconds_per_angstrom_squared * d_spacing_angstrom * d_spacing_angstrom
        + calibration.difc_microseconds_per_angstrom * d_spacing_angstrom
        + calibration.zero_microseconds
    )


def _scattering_lookup_labels(lookup_count: int, *, use_cached_keys: bool) -> tuple[str, ...]:
    aliases = ("1H", " H-2 ", "D", "nat C", "c", "O", "nat H", "2H")
    cached = ("1H", "2H", "D", "nat C", "C", "O", "nat H", "H")
    source = cached if use_cached_keys else aliases
    return tuple(source[index % len(source)] for index in range(lookup_count))


def _evaluate_scattering_lookup(labels: Sequence[str]) -> dict[str, Any]:
    checksum = 0.0
    isotopes: set[str] = set()
    source = ""
    for index, label in enumerate(labels):
        value = lookup_bound_coherent_scattering_length(label)
        checksum += (index + 1) * value.bound_coherent_fm
        isotopes.add(value.isotope)
        source = value.source
    return {
        "checksum": checksum,
        "unique_result_isotopes": sorted(isotopes),
        "source": source,
    }


def _build_magnetic_fixture(reflection_count: int) -> dict[str, Any]:
    moments = (
        MagneticMoment("mn1", (0.0, 0.0, 3.2), coordinate_frame="crystal_fractional"),
        MagneticMoment("mn2", (1.1, 0.0, -2.7), coordinate_frame="crystal_fractional"),
        MagneticMoment("mn3", (0.4, 1.3, 0.2), coordinate_frame="crystal_fractional"),
    )
    positions = (
        (0.0, 0.0, 0.0),
        (0.5, 0.5, 0.0),
        (0.25, 0.25, 0.5),
    )
    reflections = tuple(_synthetic_hkl(index) for index in range(reflection_count))
    return {
        "moments": moments,
        "positions": positions,
        "reflections": reflections,
        "propagation": PropagationVector("k1", (0.5, 0.0, 0.0)),
    }


def _evaluate_magnetic_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    reflection_checksums = []
    checksum = 0.0
    propagation = fixture["propagation"]
    for reflection_index, hkl in enumerate(fixture["reflections"]):
        q_direction = _normalized_vector(tuple(float(value) for value in hkl))
        real = 0.0
        imaginary = 0.0
        for moment, position in zip(fixture["moments"], fixture["positions"], strict=True):
            transverse = _transverse_moment_magnitude(moment.components_bohr_magneton, q_direction)
            phase = _reflection_phase_radians(hkl, position) + propagation.phase_radians(position)
            real += transverse * math.cos(phase)
            imaginary += transverse * math.sin(phase)
        intensity = real * real + imaginary * imaginary
        reflection_checksum = (reflection_index + 1) * intensity
        reflection_checksums.append(reflection_checksum)
        checksum += reflection_checksum
    return {
        "checksum": checksum,
        "reflection_checksums": reflection_checksums,
        "propagation_vector": propagation.to_dict(),
    }


def _synthetic_hkl(index: int) -> tuple[int, int, int]:
    return (index % 3 + 1, (index // 3) % 3, (index // 9) % 3)


def _reflection_phase_radians(hkl: Sequence[int], position: Sequence[float]) -> float:
    turns = sum(index * coordinate for index, coordinate in zip(hkl, position, strict=True))
    return 2.0 * math.pi * turns


def _transverse_moment_magnitude(
    components: Sequence[float],
    q_direction: Sequence[float],
) -> float:
    dot = sum(component * direction for component, direction in zip(components, q_direction, strict=True))
    magnitude_squared = sum(component * component for component in components)
    return math.sqrt(max(0.0, magnitude_squared - dot * dot))


def _normalized_vector(values: Sequence[float]) -> tuple[float, float, float]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0.0:
        raise ValueError("cannot normalize a zero vector.")
    normalized = tuple(value / norm for value in values)
    return (normalized[0], normalized[1], normalized[2])


def _build_edxrd_fixture(
    channel_count: int,
    peak_count: int,
    *,
    include_tail: bool,
) -> dict[str, Any]:
    axis = EnergyHistogramAxis.from_linear_calibration(
        channel_count=channel_count,
        offset_keV=18.0,
        gain_keV_per_channel=0.22,
    )
    two_theta_degrees = 8.0
    d_spacings = tuple(3.8 - 0.35 * index for index in range(peak_count))
    peak_energies = tuple(
        fixed_angle_bragg_energy_keV(d_spacing, two_theta_degrees)
        for d_spacing in d_spacings
    )
    return {
        "axis": axis,
        "two_theta_degrees": two_theta_degrees,
        "peak_energies_keV": peak_energies,
        "include_tail": include_tail,
    }


def _evaluate_edxrd_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    axis = fixture["axis"]
    response = [0.0 for _ in axis.centers_keV]
    for peak_index, energy in enumerate(fixture["peak_energies_keV"]):
        fwhm = 0.18 + 0.025 * peak_index
        area = 1.0 + 0.5 * peak_index
        gaussian = gaussian_profile(axis.centers_keV, center=energy, fwhm=fwhm, area=area)
        if fixture["include_tail"]:
            tail = _high_energy_tail(
                axis.centers_keV,
                center_keV=energy,
                decay_keV=0.35 + 0.05 * peak_index,
                area=0.15 * area,
            )
            response = [
                current + gaussian_value + tail_value
                for current, gaussian_value, tail_value in zip(response, gaussian, tail, strict=True)
            ]
        else:
            response = [current + value for current, value in zip(response, gaussian, strict=True)]

    return {
        "checksum": _weighted_checksum(response),
        "finite_output": all(math.isfinite(value) for value in response),
        "response_sample_count": len(response),
        "peak_energies_keV": list(fixture["peak_energies_keV"]),
    }


def _high_energy_tail(
    x_keV: Sequence[float],
    *,
    center_keV: float,
    decay_keV: float,
    area: float,
) -> list[float]:
    if decay_keV <= 0.0:
        raise ValueError("decay_keV must be positive.")
    return [
        0.0 if energy < center_keV else (area / decay_keV) * math.exp(-(energy - center_keV) / decay_keV)
        for energy in x_keV
    ]


def _weighted_checksum(values: Sequence[float]) -> float:
    return sum((index + 1) * value for index, value in enumerate(values))


def _base_environment() -> dict[str, Any]:
    return {
        "device": "cpu",
        "git_commit": _git_commit_if_available(),
        "python_version": platform.python_version(),
        "platform_machine": platform.machine(),
        "platform_processor": platform.processor(),
        "platform_system": platform.system(),
        "timing_model": {
            "compile_seconds": None,
            "warmup": "unmeasured iterations before steady-state timing",
            "steady_state": "measured iterations summarized by median/min/max wall time",
        },
    }


def _git_commit_if_available() -> str | None:
    for parent in Path(__file__).resolve().parents:
        git_path = parent / ".git"
        if git_path.is_dir():
            head_path = git_path / "HEAD"
            if not head_path.exists():
                return None
            head = head_path.read_text(encoding="utf-8").strip()
            if head.startswith("ref: "):
                ref_path = git_path / head.removeprefix("ref: ").strip()
                return ref_path.read_text(encoding="utf-8").strip() if ref_path.exists() else None
            return head or None
    return None


def _positive_int(value: int, name: str) -> None:
    _minimum_int(value, name, minimum=1)


def _nonnegative_int(value: int, name: str) -> None:
    _minimum_int(value, name, minimum=0)


def _minimum_int(value: int, name: str, *, minimum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer greater than or equal to {minimum}, got {value!r}.")
