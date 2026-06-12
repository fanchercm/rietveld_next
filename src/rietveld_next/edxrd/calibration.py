"""EDXRD channel-to-energy calibration workflow records."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import math

from rietveld_next.edxrd.axis import EnergyHistogramAxis
from rietveld_next.edxrd.bragg import fixed_angle_bragg_energy_keV


@dataclass(frozen=True)
class EDXRDCalibrationPoint:
    """Reference standard peak for channel-to-energy calibration.

    Args:
        channel: Finite detector-channel coordinate.
        energy_keV: Positive reference photon energy in keV.
        label: Non-empty standard peak label.

    Raises:
        ValueError: If the channel, energy, or label is invalid.
    """

    channel: float
    energy_keV: float
    label: str = "standard"

    def __post_init__(self) -> None:
        """Validate calibration point."""
        object.__setattr__(self, "channel", _finite_float(self.channel, "channel"))
        object.__setattr__(self, "energy_keV", _positive_float(self.energy_keV, "energy_keV"))
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError("label must be a non-empty string.")
        object.__setattr__(self, "label", self.label.strip())

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible mapping."""
        return {"channel": self.channel, "energy_keV": self.energy_keV, "label": self.label}


@dataclass(frozen=True)
class EDXRDCalibrationResult:
    """Result from fitting a channel-to-energy polynomial.

    Args:
        coefficients_keV_by_channel_power: Polynomial coefficients ordered by
            ascending detector-channel power.
        rms_residual_keV: Root-mean-square residual in keV.
        point_count: Number of standard peaks used by the workflow.
        polynomial_order: Fitted polynomial order.
        residuals_keV: Optional per-peak residuals in input order.
        standard_points: Optional standard peaks used by the fit.
        provenance: Deterministic workflow provenance labels.

    Raises:
        ValueError: If coefficients, diagnostics, or provenance are invalid.
    """

    coefficients_keV_by_channel_power: tuple[float, ...]
    rms_residual_keV: float
    point_count: int
    polynomial_order: int
    residuals_keV: tuple[float, ...] = ()
    standard_points: tuple[EDXRDCalibrationPoint, ...] = ()
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate calibration result diagnostics and provenance."""

        coefficients = _finite_float_tuple(
            self.coefficients_keV_by_channel_power,
            "coefficients_keV_by_channel_power",
        )
        if len(coefficients) < 2:
            raise ValueError("coefficients_keV_by_channel_power must contain at least two coefficients.")
        rms = _finite_float(self.rms_residual_keV, "rms_residual_keV")
        if rms < 0.0:
            raise ValueError("rms_residual_keV must be non-negative.")
        if isinstance(self.point_count, bool) or not isinstance(self.point_count, int) or self.point_count <= 0:
            raise ValueError("point_count must be a positive integer.")
        if isinstance(self.polynomial_order, bool) or not isinstance(self.polynomial_order, int):
            raise ValueError("polynomial_order must be an integer.")
        if self.polynomial_order != len(coefficients) - 1:
            raise ValueError("polynomial_order must match the coefficient count.")
        residuals = _finite_float_tuple(self.residuals_keV, "residuals_keV") if self.residuals_keV else ()
        points = _points_tuple(self.standard_points, allow_empty=True)
        if residuals and len(residuals) != self.point_count:
            raise ValueError("residuals_keV must match point_count when supplied.")
        if points and len(points) != self.point_count:
            raise ValueError("standard_points must match point_count when supplied.")
        provenance = _string_mapping(self.provenance, "provenance")
        object.__setattr__(self, "coefficients_keV_by_channel_power", coefficients)
        object.__setattr__(self, "rms_residual_keV", rms)
        object.__setattr__(self, "residuals_keV", residuals)
        object.__setattr__(self, "standard_points", points)
        object.__setattr__(self, "provenance", provenance)

    @property
    def max_abs_residual_keV(self) -> float:
        """Return the maximum absolute calibration residual in keV."""

        if not self.residuals_keV:
            return self.rms_residual_keV
        return max(abs(residual) for residual in self.residuals_keV)

    def to_axis(self, *, channel_count: int, channel_start: int = 0) -> EnergyHistogramAxis:
        """Build an energy axis from the fitted calibration."""
        return EnergyHistogramAxis.from_polynomial_calibration(
            channel_count=channel_count,
            channel_start=channel_start,
            coefficients_keV_by_channel_power=self.coefficients_keV_by_channel_power,
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "workflow": "edxrd_channel_energy_calibration",
            "polynomial_order": self.polynomial_order,
            "coefficients_keV_by_channel_power": list(self.coefficients_keV_by_channel_power),
            "rms_residual_keV": self.rms_residual_keV,
            "max_abs_residual_keV": self.max_abs_residual_keV,
            "point_count": self.point_count,
            "residuals_keV": list(self.residuals_keV),
            "standard_points": [point.to_dict() for point in self.standard_points],
            "provenance": dict(sorted(self.provenance.items())),
            "units": {
                "energy": "keV",
                "channel": "detector_channel",
                "coefficients": "keV / channel^power",
            },
        }


def fit_edxrd_channel_energy_calibration(
    points: Sequence[EDXRDCalibrationPoint],
    *,
    polynomial_order: int = 1,
    provenance: Mapping[str, str] | None = None,
) -> EDXRDCalibrationResult:
    """Fit a small deterministic channel-to-energy calibration.

    Args:
        points: Reference standard peaks.
        polynomial_order: Polynomial order, currently 1 or 2.
        provenance: Optional workflow provenance labels.

    Returns:
        Fitted calibration result.

    Raises:
        ValueError: If inputs are invalid or the fit is underdetermined.
    """
    if isinstance(polynomial_order, bool) or not isinstance(polynomial_order, int):
        raise ValueError("polynomial_order must be 1 or 2.")
    if polynomial_order not in {1, 2}:
        raise ValueError("polynomial_order must be 1 or 2.")
    point_tuple = _points_tuple(points)
    if len(point_tuple) < polynomial_order + 1:
        raise ValueError("points must contain at least polynomial_order + 1 entries.")
    channels = tuple(point.channel for point in point_tuple)
    if len(set(channels)) != len(channels):
        raise ValueError("points must not contain duplicate channels.")

    coefficients = _least_squares_polynomial(point_tuple, polynomial_order)
    residuals = tuple(point.energy_keV - _evaluate_polynomial(coefficients, point.channel) for point in point_tuple)
    rms = math.sqrt(sum(residual * residual for residual in residuals) / len(residuals))
    provenance_payload = {
        "fit_method": "unweighted_normal_equations",
        "polynomial_order": str(polynomial_order),
    }
    if provenance is not None:
        provenance_payload.update(_string_mapping(provenance, "provenance"))
    return EDXRDCalibrationResult(
        coefficients_keV_by_channel_power=coefficients,
        rms_residual_keV=rms,
        point_count=len(point_tuple),
        polynomial_order=polynomial_order,
        residuals_keV=residuals,
        standard_points=point_tuple,
        provenance=provenance_payload,
    )


def calibration_points_from_fixed_angle_standard(
    *,
    channels: Sequence[float],
    d_spacings_angstrom: Sequence[float],
    two_theta_degrees: float,
    labels: Sequence[str] | None = None,
    order: int = 1,
) -> tuple[EDXRDCalibrationPoint, ...]:
    """Create calibration points from fixed-angle Bragg standard d-spacings.

    Args:
        channels: Observed detector-channel coordinates.
        d_spacings_angstrom: Positive reference d-spacings in angstroms.
        two_theta_degrees: Fixed scattering angle in degrees two-theta.
        labels: Optional peak labels with the same length as ``channels``.
        order: Positive diffraction order.

    Returns:
        Calibration points with reference energies in keV.

    Raises:
        ValueError: If sequence lengths or physical inputs are invalid.
    """

    channel_values = _finite_float_tuple(channels, "channels")
    d_spacings = _finite_float_tuple(d_spacings_angstrom, "d_spacings_angstrom")
    if len(channel_values) != len(d_spacings):
        raise ValueError("channels and d_spacings_angstrom must have the same length.")
    label_values = _labels_tuple(labels, len(channel_values))
    return tuple(
        EDXRDCalibrationPoint(
            channel=channel,
            energy_keV=fixed_angle_bragg_energy_keV(d_spacing, two_theta_degrees, order=order),
            label=label_values[index],
        )
        for index, (channel, d_spacing) in enumerate(zip(channel_values, d_spacings, strict=True))
    )


def fit_fixed_angle_edxrd_calibration(
    *,
    channels: Sequence[float],
    d_spacings_angstrom: Sequence[float],
    two_theta_degrees: float,
    polynomial_order: int = 1,
    labels: Sequence[str] | None = None,
    order: int = 1,
    provenance: Mapping[str, str] | None = None,
) -> EDXRDCalibrationResult:
    """Fit channel-to-energy calibration from fixed-angle standard peaks.

    Args:
        channels: Observed detector-channel coordinates.
        d_spacings_angstrom: Reference standard d-spacings in angstroms.
        two_theta_degrees: Fixed scattering angle in degrees two-theta.
        polynomial_order: Calibration polynomial order, currently 1 or 2.
        labels: Optional standard-peak labels.
        order: Positive diffraction order for the Bragg conversion.
        provenance: Optional workflow provenance labels.

    Returns:
        Fitted calibration result with residuals and provenance.

    Raises:
        ValueError: If inputs are invalid or the fit is singular.
    """

    points = calibration_points_from_fixed_angle_standard(
        channels=channels,
        d_spacings_angstrom=d_spacings_angstrom,
        two_theta_degrees=two_theta_degrees,
        labels=labels,
        order=order,
    )
    workflow_provenance = {
        "reference_geometry": "fixed_angle_bragg",
        "two_theta_degrees": str(_positive_float(two_theta_degrees, "two_theta_degrees")),
        "diffraction_order": str(_positive_int(order, "order")),
    }
    if provenance is not None:
        workflow_provenance.update(_string_mapping(provenance, "provenance"))
    return fit_edxrd_channel_energy_calibration(
        points,
        polynomial_order=polynomial_order,
        provenance=workflow_provenance,
    )


def _least_squares_polynomial(points: tuple[EDXRDCalibrationPoint, ...], order: int) -> tuple[float, ...]:
    size = order + 1
    normal = [[0.0 for _ in range(size)] for _ in range(size)]
    rhs = [0.0 for _ in range(size)]
    for point in points:
        powers = [point.channel**power for power in range(size)]
        for row in range(size):
            rhs[row] += powers[row] * point.energy_keV
            for col in range(size):
                normal[row][col] += powers[row] * powers[col]
    return tuple(_solve_linear_system(normal, rhs))


def _solve_linear_system(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    n = len(rhs)
    augmented = [row[:] + [rhs_value] for row, rhs_value in zip(matrix, rhs, strict=True)]
    for pivot in range(n):
        pivot_row = max(range(pivot, n), key=lambda row: abs(augmented[row][pivot]))
        if abs(augmented[pivot_row][pivot]) < 1.0e-14:
            raise ValueError("Calibration points produce a singular polynomial fit.")
        augmented[pivot], augmented[pivot_row] = augmented[pivot_row], augmented[pivot]
        pivot_value = augmented[pivot][pivot]
        for col in range(pivot, n + 1):
            augmented[pivot][col] /= pivot_value
        for row in range(n):
            if row == pivot:
                continue
            factor = augmented[row][pivot]
            for col in range(pivot, n + 1):
                augmented[row][col] -= factor * augmented[pivot][col]
    return [augmented[row][n] for row in range(n)]


def _evaluate_polynomial(coefficients: tuple[float, ...], channel: float) -> float:
    value = 0.0
    for coefficient in reversed(coefficients):
        value = value * channel + coefficient
    return value


def _points_tuple(
    values: Sequence[EDXRDCalibrationPoint],
    *,
    allow_empty: bool = False,
) -> tuple[EDXRDCalibrationPoint, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError("points must be a sequence of EDXRDCalibrationPoint values.")
    point_tuple = tuple(values)
    if not allow_empty and not point_tuple:
        raise ValueError("points must contain at least one EDXRDCalibrationPoint.")
    for index, point in enumerate(point_tuple):
        if not isinstance(point, EDXRDCalibrationPoint):
            raise ValueError(f"points[{index}] must be an EDXRDCalibrationPoint.")
    return point_tuple


def _finite_float_tuple(values: Sequence[float], name: str) -> tuple[float, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    return tuple(_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values))


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _positive_float(value: float, name: str) -> float:
    number = _finite_float(value, name)
    if number <= 0.0:
        raise ValueError(f"{name} must be positive, got {number!r}.")
    return number


def _positive_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer.")
    if value <= 0:
        raise ValueError(f"{name} must be positive.")
    return value


def _labels_tuple(labels: Sequence[str] | None, count: int) -> tuple[str, ...]:
    if labels is None:
        return tuple(f"standard-{index + 1}" for index in range(count))
    if isinstance(labels, str) or not isinstance(labels, Sequence):
        raise ValueError("labels must be a sequence of strings when supplied.")
    if len(labels) != count:
        raise ValueError("labels must have the same length as channels.")
    return tuple(_non_empty_string(label, f"labels[{index}]") for index, label in enumerate(labels))


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
