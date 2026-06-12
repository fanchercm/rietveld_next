"""Detector response helpers for energy-dispersive X-ray diffraction."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import math

from rietveld_next.edxrd.axis import EnergyHistogramAxis


@dataclass(frozen=True)
class EDXRDResponsePeak:
    """Energy-domain stick peak supplied to a detector response model.

    Args:
        energy_keV: Positive photon energy in keV.
        area_counts: Non-negative integrated peak area in counts.
        label: Non-empty deterministic peak label.

    Raises:
        ValueError: If energy, area, or label metadata are invalid.
    """

    energy_keV: float
    area_counts: float
    label: str = "peak"

    def __post_init__(self) -> None:
        """Validate peak units and metadata."""

        object.__setattr__(self, "energy_keV", _positive_float(self.energy_keV, "energy_keV"))
        object.__setattr__(self, "area_counts", _non_negative_float(self.area_counts, "area_counts"))
        object.__setattr__(self, "label", _non_empty_string(self.label, "label"))

    def scaled(self, factor: float, *, label_suffix: str = "") -> EDXRDResponsePeak:
        """Return the same peak with area multiplied by ``factor``.

        Args:
            factor: Non-negative scale factor.
            label_suffix: Optional suffix appended to the peak label.

        Returns:
            Scaled peak record.

        Raises:
            ValueError: If the scale factor or suffix is invalid.
        """

        scale = _non_negative_float(factor, "factor")
        if not isinstance(label_suffix, str):
            raise ValueError("label_suffix must be a string.")
        return EDXRDResponsePeak(
            energy_keV=self.energy_keV,
            area_counts=self.area_counts * scale,
            label=f"{self.label}{label_suffix}",
        )

    def shifted(self, energy_shift_keV: float, *, area_factor: float, label_suffix: str) -> EDXRDResponsePeak:
        """Return an energy-shifted peak with scaled area.

        Args:
            energy_shift_keV: Energy added to the peak position in keV.
            area_factor: Non-negative area multiplier.
            label_suffix: Non-empty suffix appended to the peak label.

        Returns:
            Shifted peak record.

        Raises:
            ValueError: If the shifted energy is non-positive or metadata are
                invalid.
        """

        shift = _finite_float(energy_shift_keV, "energy_shift_keV")
        suffix = _non_empty_string(label_suffix, "label_suffix")
        return EDXRDResponsePeak(
            energy_keV=self.energy_keV + shift,
            area_counts=self.area_counts * _non_negative_float(area_factor, "area_factor"),
            label=f"{self.label}{suffix}",
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible peak record."""

        return {
            "energy_keV": self.energy_keV,
            "area_counts": self.area_counts,
            "label": self.label,
        }


@dataclass(frozen=True)
class GaussianDetectorResponse:
    """Area-preserving Gaussian detector response kernel.

    Args:
        fwhm_keV: Positive detector full width at half maximum in keV.
        label: Non-empty kernel label for provenance and component reporting.

    Raises:
        ValueError: If FWHM or label metadata are invalid.

    Example:
        >>> kernel = GaussianDetectorResponse(fwhm_keV=0.2)
        >>> round(kernel.sigma_keV, 6)
        0.084932
    """

    fwhm_keV: float
    label: str = "gaussian"

    def __post_init__(self) -> None:
        """Validate detector response width."""

        object.__setattr__(self, "fwhm_keV", _positive_float(self.fwhm_keV, "fwhm_keV"))
        object.__setattr__(self, "label", _non_empty_string(self.label, "label"))

    @property
    def sigma_keV(self) -> float:
        """Return Gaussian standard deviation in keV."""

        return self.fwhm_keV / (2.0 * math.sqrt(2.0 * math.log(2.0)))

    def density_counts_per_keV(
        self,
        energies_keV: Sequence[float],
        peak: EDXRDResponsePeak,
    ) -> tuple[float, ...]:
        """Evaluate the Gaussian response density at energy coordinates.

        Args:
            energies_keV: Energy coordinates in keV.
            peak: Stick peak to broaden.

        Returns:
            Density values in counts per keV.

        Raises:
            ValueError: If energies or peak are invalid.
        """

        energies = _positive_float_tuple(energies_keV, "energies_keV")
        response_peak = _response_peak(peak, "peak")
        sigma = self.sigma_keV
        norm = response_peak.area_counts / (sigma * math.sqrt(2.0 * math.pi))
        return tuple(
            norm * math.exp(-0.5 * ((energy - response_peak.energy_keV) / sigma) ** 2)
            for energy in energies
        )

    def integrate_peak(self, axis: EnergyHistogramAxis, peak: EDXRDResponsePeak) -> tuple[float, ...]:
        """Integrate a peak over histogram bins using Gaussian CDF edges.

        Args:
            axis: Energy histogram axis in keV.
            peak: Stick peak to broaden.

        Returns:
            Per-bin counts; the sum is the peak area captured by the axis.

        Raises:
            ValueError: If the axis or peak is invalid.
        """

        energy_axis = _energy_axis(axis)
        response_peak = _response_peak(peak, "peak")
        sigma = self.sigma_keV
        return tuple(
            response_peak.area_counts
            * (
                _normal_cdf((right - response_peak.energy_keV) / sigma)
                - _normal_cdf((left - response_peak.energy_keV) / sigma)
            )
            for left, right in zip(energy_axis.bin_edges_keV, energy_axis.bin_edges_keV[1:])
        )

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible kernel metadata."""

        return {
            "kernel": "gaussian_detector_response",
            "label": self.label,
            "fwhm_keV": self.fwhm_keV,
            "sigma_keV": self.sigma_keV,
            "units": {"energy_width": "keV", "density": "counts / keV"},
        }


@dataclass(frozen=True)
class LowEnergyTailHook:
    """Optional one-sided exponential low-energy tail response hook.

    The hook adds a normalized tail on the low-energy side of each peak. It is
    a deterministic startup fixture, not a validated detector-specific tail
    model.

    Args:
        fraction: Non-negative fraction of the input peak area assigned to the
            tail component.
        decay_keV: Positive exponential decay length in keV.
        label: Non-empty component label.
        provenance: Deterministic provenance labels.

    Raises:
        ValueError: If parameters or provenance are invalid.
    """

    fraction: float
    decay_keV: float
    label: str = "low_energy_tail"
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate tail hook parameters and provenance."""

        object.__setattr__(self, "fraction", _bounded_fraction(self.fraction, "fraction"))
        object.__setattr__(self, "decay_keV", _positive_float(self.decay_keV, "decay_keV"))
        object.__setattr__(self, "label", _non_empty_string(self.label, "label"))
        object.__setattr__(self, "provenance", _string_mapping(self.provenance, "provenance"))

    def integrate_peak(self, axis: EnergyHistogramAxis, peak: EDXRDResponsePeak) -> tuple[float, ...]:
        """Integrate the tail contribution over histogram bins.

        Args:
            axis: Energy histogram axis in keV.
            peak: Stick peak receiving the low-energy tail.

        Returns:
            Per-bin tail counts.

        Raises:
            ValueError: If the axis or peak is invalid.
        """

        energy_axis = _energy_axis(axis)
        response_peak = _response_peak(peak, "peak")
        if self.fraction == 0.0 or response_peak.area_counts == 0.0:
            return tuple(0.0 for _ in range(energy_axis.bin_count))
        tail_area = response_peak.area_counts * self.fraction
        counts: list[float] = []
        for left, right in zip(energy_axis.bin_edges_keV, energy_axis.bin_edges_keV[1:]):
            upper = min(right, response_peak.energy_keV)
            if upper <= left:
                counts.append(0.0)
                continue
            fraction_in_bin = math.exp((upper - response_peak.energy_keV) / self.decay_keV) - math.exp(
                (left - response_peak.energy_keV) / self.decay_keV
            )
            counts.append(tail_area * fraction_in_bin)
        return tuple(counts)

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible hook metadata."""

        return {
            "hook": "low_energy_tail",
            "label": self.label,
            "fraction": self.fraction,
            "decay_keV": self.decay_keV,
            "provenance": dict(sorted(self.provenance.items())),
            "limitations": "one-sided exponential startup fixture; not detector-validated",
        }


@dataclass(frozen=True)
class EscapePeakHook:
    """Optional detector escape peak correction hook.

    The hook splits each incoming stick peak into a reduced primary peak and a
    lower-energy escape peak. This preserves total area before axis truncation.

    Args:
        escape_energy_keV: Positive energy subtracted from the primary peak.
        fraction: Fraction of each peak area assigned to the escape peak.
        label: Non-empty component label.
        provenance: Deterministic provenance labels.

    Raises:
        ValueError: If parameters or provenance are invalid.
    """

    escape_energy_keV: float
    fraction: float
    label: str = "escape_peak"
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate escape hook parameters and provenance."""

        object.__setattr__(self, "escape_energy_keV", _positive_float(self.escape_energy_keV, "escape_energy_keV"))
        object.__setattr__(self, "fraction", _bounded_fraction(self.fraction, "fraction"))
        object.__setattr__(self, "label", _non_empty_string(self.label, "label"))
        object.__setattr__(self, "provenance", _string_mapping(self.provenance, "provenance"))

    def split_peaks(self, peaks: Sequence[EDXRDResponsePeak]) -> tuple[EDXRDResponsePeak, ...]:
        """Return primary and escape-peak stick records.

        Args:
            peaks: Input stick peaks.

        Returns:
            Tuple containing reduced primary peaks and escape peaks.

        Raises:
            ValueError: If an escape contribution would have non-positive
                photon energy.
        """

        response_peaks = _response_peak_tuple(peaks)
        if self.fraction == 0.0:
            return response_peaks
        split: list[EDXRDResponsePeak] = []
        for peak in response_peaks:
            escape_energy = peak.energy_keV - self.escape_energy_keV
            if escape_energy <= 0.0:
                raise ValueError(
                    "escape_energy_keV must be smaller than every peak energy when escape fraction is positive."
                )
            split.append(peak.scaled(1.0 - self.fraction, label_suffix=":primary"))
            split.append(
                EDXRDResponsePeak(
                    energy_keV=escape_energy,
                    area_counts=peak.area_counts * self.fraction,
                    label=f"{peak.label}:{self.label}",
                )
            )
        return tuple(split)

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible hook metadata."""

        return {
            "hook": "escape_peak",
            "label": self.label,
            "escape_energy_keV": self.escape_energy_keV,
            "fraction": self.fraction,
            "provenance": dict(sorted(self.provenance.items())),
            "limitations": "single fixed escape energy startup fixture; not detector-validated",
        }


@dataclass(frozen=True)
class DeadTimeMetadata:
    """Dead-time correction metadata attached to an EDXRD response result.

    This record documents whether upstream count data were corrected. It does
    not apply a dead-time correction numerically.

    Args:
        model: Dead-time model label such as ``"nonparalyzable"``.
        correction_applied: Whether a dead-time correction has already been
            applied upstream.
        dead_time_seconds: Optional non-negative detector dead time in seconds.
        observed_count_rate_hz: Optional non-negative observed count rate.
        correction_factor: Optional positive multiplicative correction factor.
        provenance: Deterministic provenance labels.

    Raises:
        ValueError: If metadata values are invalid.
    """

    model: str
    correction_applied: bool
    dead_time_seconds: float | None = None
    observed_count_rate_hz: float | None = None
    correction_factor: float | None = None
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate dead-time metadata."""

        object.__setattr__(self, "model", _non_empty_string(self.model, "model"))
        if not isinstance(self.correction_applied, bool):
            raise ValueError("correction_applied must be a boolean.")
        if self.dead_time_seconds is not None:
            object.__setattr__(
                self,
                "dead_time_seconds",
                _non_negative_float(self.dead_time_seconds, "dead_time_seconds"),
            )
        if self.observed_count_rate_hz is not None:
            object.__setattr__(
                self,
                "observed_count_rate_hz",
                _non_negative_float(self.observed_count_rate_hz, "observed_count_rate_hz"),
            )
        if self.correction_factor is not None:
            object.__setattr__(self, "correction_factor", _positive_float(self.correction_factor, "correction_factor"))
        object.__setattr__(self, "provenance", _string_mapping(self.provenance, "provenance"))

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible dead-time metadata."""

        payload: dict[str, object] = {
            "metadata_type": "edxrd_dead_time",
            "model": self.model,
            "correction_applied": self.correction_applied,
            "units": {
                "dead_time": "s",
                "observed_count_rate": "Hz",
                "correction_factor": "dimensionless",
            },
            "provenance": dict(sorted(self.provenance.items())),
        }
        if self.dead_time_seconds is not None:
            payload["dead_time_seconds"] = self.dead_time_seconds
        if self.observed_count_rate_hz is not None:
            payload["observed_count_rate_hz"] = self.observed_count_rate_hz
        if self.correction_factor is not None:
            payload["correction_factor"] = self.correction_factor
        return payload


@dataclass(frozen=True)
class DetectorResponseResult:
    """Binned detector response counts and provenance."""

    bin_counts: tuple[float, ...]
    component_counts: Mapping[str, tuple[float, ...]]
    provenance: Mapping[str, str] = field(default_factory=dict)
    dead_time: DeadTimeMetadata | None = None

    def __post_init__(self) -> None:
        """Validate response result arrays and metadata."""

        counts = _non_negative_float_tuple(self.bin_counts, "bin_counts")
        components = _component_mapping(self.component_counts, len(counts))
        provenance = _string_mapping(self.provenance, "provenance")
        if self.dead_time is not None and not isinstance(self.dead_time, DeadTimeMetadata):
            raise ValueError("dead_time must be DeadTimeMetadata when supplied.")
        object.__setattr__(self, "bin_counts", counts)
        object.__setattr__(self, "component_counts", components)
        object.__setattr__(self, "provenance", provenance)

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible response output."""

        payload: dict[str, object] = {
            "result_type": "edxrd_detector_response",
            "bin_counts": list(self.bin_counts),
            "component_counts": {
                label: list(counts)
                for label, counts in sorted(self.component_counts.items())
            },
            "provenance": dict(sorted(self.provenance.items())),
            "units": {"bin_counts": "counts"},
        }
        if self.dead_time is not None:
            payload["dead_time"] = self.dead_time.to_dict()
        return payload


@dataclass(frozen=True)
class DetectorResponseModel:
    """Composable EDXRD detector response model.

    Args:
        gaussian: Gaussian core detector response kernel.
        low_energy_tail: Optional low-energy tail hook.
        escape_peak: Optional escape peak hook.
        dead_time: Optional dead-time correction metadata.
        provenance: Deterministic model-level provenance labels.

    Raises:
        ValueError: If components or provenance are invalid.
    """

    gaussian: GaussianDetectorResponse
    low_energy_tail: LowEnergyTailHook | None = None
    escape_peak: EscapePeakHook | None = None
    dead_time: DeadTimeMetadata | None = None
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate detector response components."""

        if not isinstance(self.gaussian, GaussianDetectorResponse):
            raise ValueError("gaussian must be a GaussianDetectorResponse.")
        if self.low_energy_tail is not None and not isinstance(self.low_energy_tail, LowEnergyTailHook):
            raise ValueError("low_energy_tail must be a LowEnergyTailHook when supplied.")
        if self.escape_peak is not None and not isinstance(self.escape_peak, EscapePeakHook):
            raise ValueError("escape_peak must be an EscapePeakHook when supplied.")
        if self.dead_time is not None and not isinstance(self.dead_time, DeadTimeMetadata):
            raise ValueError("dead_time must be DeadTimeMetadata when supplied.")
        object.__setattr__(self, "provenance", _string_mapping(self.provenance, "provenance"))

    def evaluate(
        self,
        axis: EnergyHistogramAxis,
        peaks: Sequence[EDXRDResponsePeak],
    ) -> DetectorResponseResult:
        """Evaluate detector response counts for energy-domain stick peaks.

        Args:
            axis: Energy histogram axis in keV.
            peaks: Input energy-domain stick peaks. Crystallographic peak
                generation and intensity calculations are intentionally outside
                this API boundary.

        Returns:
            Binned detector response result with component counts and
            provenance.

        Raises:
            ValueError: If inputs or hook transformations are invalid.
        """

        energy_axis = _energy_axis(axis)
        response_peaks = _response_peak_tuple(peaks)
        if self.escape_peak is not None:
            response_peaks = self.escape_peak.split_peaks(response_peaks)

        gaussian_counts = _zero_counts(energy_axis.bin_count)
        tail_counts = _zero_counts(energy_axis.bin_count)
        for peak in response_peaks:
            gaussian_counts = _add_counts(gaussian_counts, self.gaussian.integrate_peak(energy_axis, peak))
            if self.low_energy_tail is not None:
                tail_counts = _add_counts(tail_counts, self.low_energy_tail.integrate_peak(energy_axis, peak))

        component_counts: dict[str, tuple[float, ...]] = {self.gaussian.label: gaussian_counts}
        if self.low_energy_tail is not None:
            component_counts[self.low_energy_tail.label] = tail_counts
        total = gaussian_counts
        if self.low_energy_tail is not None:
            total = _add_counts(total, tail_counts)

        provenance = {
            "response_model": "edxrd_detector_response.v1",
            "gaussian_kernel": self.gaussian.label,
        }
        if self.escape_peak is not None:
            provenance["escape_peak_hook"] = self.escape_peak.label
            provenance.update({f"escape_peak.{key}": value for key, value in self.escape_peak.provenance.items()})
        if self.low_energy_tail is not None:
            provenance["low_energy_tail_hook"] = self.low_energy_tail.label
            provenance.update(
                {f"low_energy_tail.{key}": value for key, value in self.low_energy_tail.provenance.items()}
            )
        provenance.update(self.provenance)
        return DetectorResponseResult(
            bin_counts=total,
            component_counts=component_counts,
            provenance=provenance,
            dead_time=self.dead_time,
        )

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible model metadata."""

        payload: dict[str, object] = {
            "model": "edxrd_detector_response.v1",
            "gaussian": self.gaussian.to_dict(),
            "provenance": dict(sorted(self.provenance.items())),
            "limitations": (
                "Startup detector response API for synthetic tests; detector-specific "
                "tail, escape, pile-up, and nonlinearity validation remain future work; "
                "tail and escape hooks are not detector-validated."
            ),
        }
        if self.low_energy_tail is not None:
            payload["low_energy_tail"] = self.low_energy_tail.to_dict()
        if self.escape_peak is not None:
            payload["escape_peak"] = self.escape_peak.to_dict()
        if self.dead_time is not None:
            payload["dead_time"] = self.dead_time.to_dict()
        return payload


def _energy_axis(axis: EnergyHistogramAxis) -> EnergyHistogramAxis:
    if not isinstance(axis, EnergyHistogramAxis):
        raise ValueError("axis must be an EnergyHistogramAxis.")
    return axis


def _response_peak(value: EDXRDResponsePeak, name: str) -> EDXRDResponsePeak:
    if not isinstance(value, EDXRDResponsePeak):
        raise ValueError(f"{name} must be an EDXRDResponsePeak.")
    return value


def _response_peak_tuple(values: Sequence[EDXRDResponsePeak]) -> tuple[EDXRDResponsePeak, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError("peaks must be a sequence of EDXRDResponsePeak values.")
    peaks = tuple(values)
    if not peaks:
        raise ValueError("peaks must contain at least one EDXRDResponsePeak.")
    for index, peak in enumerate(peaks):
        _response_peak(peak, f"peaks[{index}]")
    return peaks


def _component_mapping(values: Mapping[str, tuple[float, ...]], bin_count: int) -> dict[str, tuple[float, ...]]:
    if not isinstance(values, Mapping):
        raise ValueError("component_counts must be a mapping.")
    components: dict[str, tuple[float, ...]] = {}
    for label, counts in values.items():
        key = _non_empty_string(label, "component_counts key")
        component = _non_negative_float_tuple(counts, f"component_counts[{key!r}]")
        if len(component) != bin_count:
            raise ValueError("component_counts entries must match bin_counts length.")
        components[key] = component
    if not components:
        raise ValueError("component_counts must not be empty.")
    return dict(sorted(components.items()))


def _zero_counts(count: int) -> tuple[float, ...]:
    return tuple(0.0 for _ in range(count))


def _add_counts(left: tuple[float, ...], right: tuple[float, ...]) -> tuple[float, ...]:
    if len(left) != len(right):
        raise ValueError("count arrays must have the same length.")
    return tuple(left_value + right_value for left_value, right_value in zip(left, right, strict=True))


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _positive_float_tuple(values: Sequence[float], name: str) -> tuple[float, ...]:
    numbers = _finite_float_tuple(values, name)
    if any(value <= 0.0 for value in numbers):
        raise ValueError(f"{name} values must be positive keV values.")
    return numbers


def _non_negative_float_tuple(values: Sequence[float], name: str) -> tuple[float, ...]:
    numbers = _finite_float_tuple(values, name)
    if any(value < 0.0 for value in numbers):
        raise ValueError(f"{name} values must be non-negative.")
    return numbers


def _finite_float_tuple(values: Sequence[float], name: str) -> tuple[float, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    return tuple(_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values))


def _bounded_fraction(value: float, name: str) -> float:
    fraction = _finite_float(value, name)
    if fraction < 0.0 or fraction > 1.0:
        raise ValueError(f"{name} must be between 0 and 1.")
    return fraction


def _positive_float(value: float, name: str) -> float:
    number = _finite_float(value, name)
    if number <= 0.0:
        raise ValueError(f"{name} must be positive, got {number!r}.")
    return number


def _non_negative_float(value: float, name: str) -> float:
    number = _finite_float(value, name)
    if number < 0.0:
        raise ValueError(f"{name} must be non-negative, got {number!r}.")
    return number


def _finite_float(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _non_empty_string(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value.strip()


def _string_mapping(values: Mapping[str, str], name: str) -> dict[str, str]:
    if not isinstance(values, Mapping):
        raise ValueError(f"{name} must be a mapping.")
    payload: dict[str, str] = {}
    for key, value in values.items():
        payload[_non_empty_string(key, f"{name} key")] = _non_empty_string(value, f"{name}[{key!r}]")
    return dict(sorted(payload.items()))
