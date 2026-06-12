"""Zero-shift calibration workflow helpers for CW X-ray instruments."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math

from rietveld_next.xray.wavelength import bragg_two_theta_degrees, validate_wavelength_angstrom


@dataclass(frozen=True)
class ZeroShiftCalibrationPoint:
    """Reference peak used to estimate a two-theta zero shift.

    Args:
        d_spacing_angstrom: Reference lattice-plane spacing in angstroms.
        observed_two_theta_degrees: Observed peak position in degrees
            two-theta.
        weight: Positive dimensionless point weight.
    """

    d_spacing_angstrom: float
    observed_two_theta_degrees: float
    weight: float = 1.0

    def __post_init__(self) -> None:
        """Validate point values."""
        d_spacing = _positive_float(self.d_spacing_angstrom, "d_spacing_angstrom")
        observed = _finite_float(self.observed_two_theta_degrees, "observed_two_theta_degrees")
        weight = _positive_float(self.weight, "weight")
        object.__setattr__(self, "d_spacing_angstrom", d_spacing)
        object.__setattr__(self, "observed_two_theta_degrees", observed)
        object.__setattr__(self, "weight", weight)

    def to_dict(self) -> dict[str, float]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "d_spacing_angstrom": self.d_spacing_angstrom,
            "observed_two_theta_degrees": self.observed_two_theta_degrees,
            "weight": self.weight,
        }


@dataclass(frozen=True)
class ZeroShiftCalibrationResult:
    """Result from a deterministic zero-shift calibration workflow.

    Args:
        zero_shift_degrees: Weighted mean observed-minus-calculated shift.
        rms_residual_degrees: Weighted RMS residual after applying the shift.
        point_count: Number of reference peaks.
        wavelength_angstrom: Incident wavelength used for Bragg positions.
        residuals_degrees: Per-point residuals after applying the shift.
    """

    zero_shift_degrees: float
    rms_residual_degrees: float
    point_count: int
    wavelength_angstrom: float
    residuals_degrees: tuple[float, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "workflow": "cw_xray_zero_shift_calibration",
            "zero_shift_degrees": self.zero_shift_degrees,
            "rms_residual_degrees": self.rms_residual_degrees,
            "point_count": self.point_count,
            "wavelength_angstrom": self.wavelength_angstrom,
            "residuals_degrees": list(self.residuals_degrees),
            "units": {
                "zero_shift": "degree_two_theta",
                "rms_residual": "degree_two_theta",
                "wavelength": "angstrom",
            },
        }


def calibrate_zero_shift(
    points: Sequence[ZeroShiftCalibrationPoint],
    *,
    wavelength_angstrom: float,
    order: int = 1,
) -> ZeroShiftCalibrationResult:
    """Estimate a constant two-theta zero shift from reference peaks.

    Args:
        points: Reference peaks with known d-spacing and observed position.
        wavelength_angstrom: Incident wavelength in angstroms.
        order: Positive diffraction order used for all points.

    Returns:
        Zero-shift calibration result with residual diagnostics.

    Raises:
        ValueError: If inputs are malformed or no points are supplied.
    """
    wavelength = validate_wavelength_angstrom(wavelength_angstrom)
    if isinstance(order, bool) or not isinstance(order, int) or order <= 0:
        raise ValueError("order must be a positive integer.")
    if isinstance(points, str) or not isinstance(points, Sequence):
        raise ValueError("points must be a sequence of ZeroShiftCalibrationPoint values.")
    if not points:
        raise ValueError("points must contain at least one calibration point.")
    point_tuple: tuple[ZeroShiftCalibrationPoint, ...] = tuple(points)
    for index, point in enumerate(point_tuple):
        if not isinstance(point, ZeroShiftCalibrationPoint):
            raise ValueError(f"points[{index}] must be a ZeroShiftCalibrationPoint.")

    shifts: list[float] = []
    total_weight = 0.0
    weighted_shift_sum = 0.0
    for point in point_tuple:
        calculated = bragg_two_theta_degrees(point.d_spacing_angstrom, wavelength, order=order)
        shift = point.observed_two_theta_degrees - calculated
        shifts.append(shift)
        total_weight += point.weight
        weighted_shift_sum += point.weight * shift
    zero_shift = weighted_shift_sum / total_weight
    residuals = tuple(shift - zero_shift for shift in shifts)
    rms = math.sqrt(sum(point.weight * residual**2 for point, residual in zip(point_tuple, residuals, strict=True)) / total_weight)
    return ZeroShiftCalibrationResult(
        zero_shift_degrees=zero_shift,
        rms_residual_degrees=rms,
        point_count=len(point_tuple),
        wavelength_angstrom=wavelength,
        residuals_degrees=residuals,
    )


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _positive_float(value: float, name: str) -> float:
    number = _finite_float(value, name)
    if number <= 0.0:
        raise ValueError(f"{name} must be positive, got {number!r}.")
    return number
