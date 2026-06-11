"""Deterministic synthetic datasets for profile benchmark smoke runs."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Any


@dataclass(frozen=True)
class ProfileDatasetPreset:
    """Synthetic Gaussian profile dataset size preset.

    Args:
        name: Preset name.
        sample_count: Number of x-axis samples.
        peak_count: Number of Gaussian peaks.
        x_min_degrees: Minimum two-theta axis value in degrees.
        x_max_degrees: Maximum two-theta axis value in degrees.

    Example:
        >>> profile_dataset_presets()["small"].sample_count
        128
    """

    name: str
    sample_count: int
    peak_count: int
    x_min_degrees: float
    x_max_degrees: float

    def __post_init__(self) -> None:
        """Validate preset bounds and counts."""
        _validate_slug(self.name, "name")
        _positive_int(self.sample_count, "sample_count")
        _nonnegative_int(self.peak_count, "peak_count")
        _finite_number(self.x_min_degrees, "x_min_degrees")
        _finite_number(self.x_max_degrees, "x_max_degrees")
        if self.sample_count < 2:
            raise ValueError("sample_count must be at least 2 to define an axis interval.")
        if self.x_min_degrees >= self.x_max_degrees:
            raise ValueError("x_min_degrees must be less than x_max_degrees.")


@dataclass(frozen=True)
class GaussianPeak:
    """Gaussian peak parameters used by a synthetic profile dataset.

    Args:
        position_degrees: Peak center in degrees two-theta.
        amplitude_counts: Peak amplitude in arbitrary counts.
        fwhm_degrees: Full width at half maximum in degrees two-theta.
    """

    position_degrees: float
    amplitude_counts: float
    fwhm_degrees: float

    def __post_init__(self) -> None:
        """Validate finite, physically positive peak parameters."""
        _finite_number(self.position_degrees, "position_degrees")
        _positive_number(self.amplitude_counts, "amplitude_counts")
        _positive_number(self.fwhm_degrees, "fwhm_degrees")

    def to_dict(self) -> dict[str, float]:
        """Return a deterministic JSON-compatible peak mapping."""
        return {
            "position_degrees": self.position_degrees,
            "amplitude_counts": self.amplitude_counts,
            "fwhm_degrees": self.fwhm_degrees,
        }


@dataclass(frozen=True)
class SyntheticProfileDataset:
    """Synthetic Gaussian profile dataset for benchmark inputs.

    Args:
        x_degrees: Two-theta axis values in degrees.
        intensities_counts: Synthetic profile intensities in arbitrary counts.
        peaks: Gaussian peak definitions used to build the profile.
        metadata: Reproducibility metadata including seed, units, and preset.
    """

    x_degrees: tuple[float, ...]
    intensities_counts: tuple[float, ...]
    peaks: tuple[GaussianPeak, ...]
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        """Validate dataset shapes and JSON-compatible metadata."""
        if len(self.x_degrees) != len(self.intensities_counts):
            raise ValueError("x_degrees and intensities_counts must have the same length.")
        if len(self.x_degrees) < 2:
            raise ValueError("dataset axis must contain at least two samples.")
        for index, value in enumerate(self.x_degrees):
            _finite_number(value, f"x_degrees[{index}]")
        for index, value in enumerate(self.intensities_counts):
            _finite_number(value, f"intensities_counts[{index}]")
        _json_compatible(self.metadata, "metadata")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible dataset summary."""
        return {
            "x_degrees": list(self.x_degrees),
            "intensities_counts": list(self.intensities_counts),
            "peaks": [peak.to_dict() for peak in self.peaks],
            "metadata": dict(sorted(self.metadata.items())),
        }

    def checksum(self) -> float:
        """Return a deterministic lightweight checksum for benchmark metadata."""
        return sum(self.intensities_counts) + sum(peak.position_degrees for peak in self.peaks)


def profile_dataset_presets() -> dict[str, ProfileDatasetPreset]:
    """Return deterministic Gaussian profile dataset presets.

    The large preset is opt-in for benchmark runners and is not used by the
    default package-local tests.

    Returns:
        Mapping from preset name to preset definition.
    """
    return {
        "small": ProfileDatasetPreset("small", sample_count=128, peak_count=3, x_min_degrees=10.0, x_max_degrees=80.0),
        "medium": ProfileDatasetPreset("medium", sample_count=2048, peak_count=12, x_min_degrees=5.0, x_max_degrees=120.0),
        "large": ProfileDatasetPreset("large", sample_count=16384, peak_count=48, x_min_degrees=2.0, x_max_degrees=160.0),
    }


def generate_synthetic_gaussian_profile_dataset(
    *,
    size: str = "small",
    seed: int = 0,
    variant: str = "synthetic",
    preset: ProfileDatasetPreset | None = None,
) -> SyntheticProfileDataset:
    """Generate a deterministic synthetic Gaussian profile dataset.

    Args:
        size: Preset size name. Ignored when ``preset`` is provided, except for
            validation and metadata if the preset has the same name.
        seed: Integer pseudo-random seed recorded in metadata.
        variant: Variant slug recorded in metadata.
        preset: Optional explicit preset for edge-case tests.

    Returns:
        Synthetic profile dataset with explicit units and reproduction metadata.

    Raises:
        ValueError: If the preset, seed, or variant is invalid.

    Example:
        >>> dataset = generate_synthetic_gaussian_profile_dataset(size="small", seed=7)
        >>> dataset.metadata["seed"]
        7
    """
    _nonnegative_int(seed, "seed")
    _validate_slug(variant, "variant")
    presets = profile_dataset_presets()
    if preset is None:
        if size not in presets:
            raise ValueError(f"size must be one of {sorted(presets)}, got {size!r}.")
        selected = presets[size]
    else:
        selected = preset
        if size != selected.name:
            raise ValueError(f"size {size!r} must match explicit preset name {selected.name!r}.")

    rng = random.Random(seed)
    axis = _linspace(selected.x_min_degrees, selected.x_max_degrees, selected.sample_count)
    peaks = tuple(_generate_peak(rng, selected) for _ in range(selected.peak_count))
    sorted_peaks = tuple(sorted(peaks, key=lambda peak: peak.position_degrees))
    intensities = tuple(_profile_intensity(x_value, sorted_peaks) for x_value in axis)
    metadata = {
        "dataset_kind": "synthetic_gaussian_profile",
        "seed": seed,
        "size": selected.name,
        "variant": variant,
        "sample_count": selected.sample_count,
        "peak_count": selected.peak_count,
        "x_unit": "degree_two_theta",
        "intensity_unit": "arbitrary_count",
        "position_unit": "degree_two_theta",
        "width_unit": "degree_two_theta_fwhm",
        "generator": "rietveld_next.benchmarks.datasets.generate_synthetic_gaussian_profile_dataset",
    }
    return SyntheticProfileDataset(
        x_degrees=axis,
        intensities_counts=intensities,
        peaks=sorted_peaks,
        metadata=metadata,
    )


def _generate_peak(rng: random.Random, preset: ProfileDatasetPreset) -> GaussianPeak:
    axis_span = preset.x_max_degrees - preset.x_min_degrees
    margin = 0.05 * axis_span
    position = rng.uniform(preset.x_min_degrees + margin, preset.x_max_degrees - margin)
    amplitude = rng.uniform(100.0, 1000.0)
    fwhm = rng.uniform(0.05, 0.25) * max(1.0, axis_span / max(preset.peak_count, 1))
    return GaussianPeak(
        position_degrees=position,
        amplitude_counts=amplitude,
        fwhm_degrees=fwhm,
    )


def _profile_intensity(x_value: float, peaks: tuple[GaussianPeak, ...]) -> float:
    total = 0.0
    for peak in peaks:
        sigma = peak.fwhm_degrees / (2.0 * math.sqrt(2.0 * math.log(2.0)))
        z = (x_value - peak.position_degrees) / sigma
        total += peak.amplitude_counts * math.exp(-0.5 * z * z)
    return total


def _linspace(start: float, stop: float, count: int) -> tuple[float, ...]:
    if count == 1:
        return (start,)
    step = (stop - start) / float(count - 1)
    return tuple(start + step * index for index in range(count))


def _finite_number(value: float, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")


def _positive_number(value: float, name: str) -> None:
    _finite_number(value, name)
    if value <= 0.0:
        raise ValueError(f"{name} must be positive, got {value!r}.")


def _positive_int(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value!r}.")


def _nonnegative_int(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer, got {value!r}.")


def _validate_slug(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.replace("_", "a").isalnum() or not value[0].isalpha() or value.lower() != value:
        raise ValueError(f"{field_name} must be a lowercase slug using letters, digits, or underscores, got {value!r}.")


def _json_compatible(value: Any, name: str) -> None:
    if value is None or isinstance(value, str | bool):
        return
    if isinstance(value, int | float) and not isinstance(value, bool):
        _finite_number(value, name)
        return
    if isinstance(value, list | tuple):
        for index, item in enumerate(value):
            _json_compatible(item, f"{name}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{name} keys must be strings, got {key!r}.")
            _json_compatible(item, f"{name}.{key}")
        return
    raise ValueError(f"{name} must be JSON-compatible, got {value!r}.")
