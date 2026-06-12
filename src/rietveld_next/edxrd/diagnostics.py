"""Residual diagnostics for EDXRD synthetic and refinement workflows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import math

from rietveld_next.edxrd.axis import EnergyHistogramAxis


@dataclass(frozen=True)
class EDXRDResidualDiagnostics:
    """Residual summary for an EDXRD observed/calculated spectrum pair."""

    residuals_counts: tuple[float, ...]
    weighted_residuals: tuple[float, ...]
    rmse_counts: float
    mean_residual_counts: float
    max_abs_residual_counts: float
    reduced_chi_square: float | None
    channel_count: int
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate residual diagnostic arrays and scalar metrics."""

        residuals = _finite_float_tuple(self.residuals_counts, "residuals_counts")
        weighted = _finite_float_tuple(self.weighted_residuals, "weighted_residuals")
        if len(residuals) != len(weighted):
            raise ValueError("weighted_residuals must match residuals_counts length.")
        if isinstance(self.channel_count, bool) or not isinstance(self.channel_count, int) or self.channel_count <= 0:
            raise ValueError("channel_count must be a positive integer.")
        if len(residuals) != self.channel_count:
            raise ValueError("channel_count must match residual vector length.")
        object.__setattr__(self, "residuals_counts", residuals)
        object.__setattr__(self, "weighted_residuals", weighted)
        object.__setattr__(self, "rmse_counts", _non_negative_float(self.rmse_counts, "rmse_counts"))
        object.__setattr__(
            self,
            "mean_residual_counts",
            _finite_float(self.mean_residual_counts, "mean_residual_counts"),
        )
        object.__setattr__(
            self,
            "max_abs_residual_counts",
            _non_negative_float(self.max_abs_residual_counts, "max_abs_residual_counts"),
        )
        if self.reduced_chi_square is not None:
            object.__setattr__(
                self,
                "reduced_chi_square",
                _non_negative_float(self.reduced_chi_square, "reduced_chi_square"),
            )
        object.__setattr__(self, "provenance", _string_mapping(self.provenance, "provenance"))

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible residual diagnostics."""

        return {
            "diagnostic_type": "edxrd_residual_diagnostics",
            "channel_count": self.channel_count,
            "residuals_counts": list(self.residuals_counts),
            "weighted_residuals": list(self.weighted_residuals),
            "rmse_counts": self.rmse_counts,
            "mean_residual_counts": self.mean_residual_counts,
            "max_abs_residual_counts": self.max_abs_residual_counts,
            "reduced_chi_square": self.reduced_chi_square,
            "units": {
                "observed": "counts",
                "calculated": "counts",
                "residual": "counts",
                "weighted_residual": "standard_uncertainty",
            },
            "residual_convention": "observed - calculated",
            "provenance": dict(sorted(self.provenance.items())),
        }


def compute_edxrd_residual_diagnostics(
    axis: EnergyHistogramAxis,
    observed_counts: Sequence[float],
    calculated_counts: Sequence[float],
    *,
    uncertainties_counts: Sequence[float] | None = None,
    fitted_parameter_count: int = 0,
    provenance: Mapping[str, str] | None = None,
) -> EDXRDResidualDiagnostics:
    """Compute deterministic EDXRD residual diagnostics.

    Args:
        axis: Energy histogram axis whose bin count defines the spectrum shape.
        observed_counts: Non-negative observed counts.
        calculated_counts: Non-negative calculated counts.
        uncertainties_counts: Optional positive standard uncertainties in
            counts. When omitted, unweighted residuals are reused.
        fitted_parameter_count: Number of fitted parameters for reduced
            chi-square degrees of freedom.
        provenance: Optional deterministic provenance labels.

    Returns:
        Residual diagnostics using ``observed - calculated`` convention.

    Raises:
        ValueError: If array lengths, count bounds, uncertainties, or degrees
            of freedom metadata are invalid.
    """

    energy_axis = _axis(axis)
    observed = _non_negative_float_tuple(observed_counts, "observed_counts")
    calculated = _non_negative_float_tuple(calculated_counts, "calculated_counts")
    if len(observed) != energy_axis.bin_count:
        raise ValueError("observed_counts length must match axis bin_count.")
    if len(calculated) != energy_axis.bin_count:
        raise ValueError("calculated_counts length must match axis bin_count.")
    residuals = tuple(obs - calc for obs, calc in zip(observed, calculated, strict=True))
    if uncertainties_counts is None:
        weighted = residuals
        reduced_chi_square = None
    else:
        uncertainties = _positive_float_tuple(uncertainties_counts, "uncertainties_counts")
        if len(uncertainties) != energy_axis.bin_count:
            raise ValueError("uncertainties_counts length must match axis bin_count.")
        weighted = tuple(residual / sigma for residual, sigma in zip(residuals, uncertainties, strict=True))
        fitted_count = _non_negative_int(fitted_parameter_count, "fitted_parameter_count")
        dof = energy_axis.bin_count - fitted_count
        reduced_chi_square = None if dof <= 0 else sum(value * value for value in weighted) / dof
    rmse = math.sqrt(sum(residual * residual for residual in residuals) / len(residuals))
    mean = sum(residuals) / len(residuals)
    max_abs = max(abs(residual) for residual in residuals)
    return EDXRDResidualDiagnostics(
        residuals_counts=residuals,
        weighted_residuals=weighted,
        rmse_counts=rmse,
        mean_residual_counts=mean,
        max_abs_residual_counts=max_abs,
        reduced_chi_square=reduced_chi_square,
        channel_count=energy_axis.bin_count,
        provenance={} if provenance is None else provenance,
    )


def _axis(value: EnergyHistogramAxis) -> EnergyHistogramAxis:
    if not isinstance(value, EnergyHistogramAxis):
        raise ValueError("axis must be an EnergyHistogramAxis.")
    return value


def _positive_float_tuple(values: Sequence[float], name: str) -> tuple[float, ...]:
    numbers = _finite_float_tuple(values, name)
    if any(value <= 0.0 for value in numbers):
        raise ValueError(f"{name} values must be positive.")
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


def _non_negative_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer.")
    return value


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
