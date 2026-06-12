"""Structured uncertainty checks for neutron reduced data."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class NeutronUncertaintyDiagnostic:
    """One neutron uncertainty diagnostic message."""

    severity: str
    code: str
    message: str
    index: int | None = None

    def __post_init__(self) -> None:
        """Validate diagnostic fields."""

        severity = _non_empty_string(self.severity, "severity")
        if severity not in {"warning", "error"}:
            raise ValueError("severity must be 'warning' or 'error'.")
        object.__setattr__(self, "severity", severity)
        object.__setattr__(self, "code", _non_empty_string(self.code, "code"))
        object.__setattr__(self, "message", _non_empty_string(self.message, "message"))
        if self.index is not None:
            if isinstance(self.index, bool) or not isinstance(self.index, int) or self.index < 0:
                raise ValueError("index must be a non-negative integer or None.")

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible diagnostic metadata."""

        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "index": self.index,
        }


@dataclass(frozen=True)
class NeutronUncertaintyCheck:
    """Result of neutron uncertainty validation."""

    status: str
    point_count: int
    sigma_unit: str
    minimum_relative_sigma: float
    diagnostics: Sequence[NeutronUncertaintyDiagnostic]

    def __post_init__(self) -> None:
        """Validate uncertainty-check result metadata."""

        status = _non_empty_string(self.status, "status")
        if status not in {"ok", "warning", "error"}:
            raise ValueError("status must be 'ok', 'warning', or 'error'.")
        if isinstance(self.point_count, bool) or not isinstance(self.point_count, int) or self.point_count < 0:
            raise ValueError("point_count must be a non-negative integer.")
        minimum = _finite_float(self.minimum_relative_sigma, "minimum_relative_sigma")
        if minimum < 0.0:
            raise ValueError("minimum_relative_sigma must be non-negative.")
        diagnostics = tuple(self.diagnostics)
        for index, diagnostic in enumerate(diagnostics):
            if not isinstance(diagnostic, NeutronUncertaintyDiagnostic):
                raise ValueError(f"diagnostics[{index}] must be a NeutronUncertaintyDiagnostic.")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "sigma_unit", _non_empty_string(self.sigma_unit, "sigma_unit"))
        object.__setattr__(self, "minimum_relative_sigma", minimum)
        object.__setattr__(self, "diagnostics", diagnostics)

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible uncertainty-check metadata."""

        return {
            "status": self.status,
            "point_count": self.point_count,
            "sigma_unit": self.sigma_unit,
            "minimum_relative_sigma": self.minimum_relative_sigma,
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
        }


def check_neutron_uncertainties(
    observed: Sequence[float],
    sigma: Sequence[float],
    *,
    minimum_relative_sigma: float = 1.0e-6,
    sigma_unit: str = "counts",
) -> NeutronUncertaintyCheck:
    """Check reduced neutron standard uncertainties.

    Args:
        observed: Observed reduced intensities.
        sigma: Standard uncertainties in ``sigma_unit``.
        minimum_relative_sigma: Warning floor relative to
            ``max(abs(observed[i]), 1)``.
        sigma_unit: Unit label for uncertainties.

    Returns:
        Structured check result. Non-positive, non-finite, and mismatched
        uncertainty arrays are reported as ``status="error"`` rather than
        silently repaired.

    Raises:
        ValueError: If inputs are not sequences or configuration is invalid.
    """

    minimum = _finite_float(minimum_relative_sigma, "minimum_relative_sigma")
    if minimum < 0.0:
        raise ValueError("minimum_relative_sigma must be non-negative.")
    observed_values = _number_sequence(observed, "observed")
    sigma_values = _number_sequence(sigma, "sigma")
    diagnostics: list[NeutronUncertaintyDiagnostic] = []
    if len(observed_values) != len(sigma_values):
        diagnostics.append(
            NeutronUncertaintyDiagnostic(
                severity="error",
                code="sigma_length_mismatch",
                message="sigma must have the same length as observed.",
            )
        )
        return _result(len(observed_values), sigma_unit, minimum, diagnostics)
    for index, value in enumerate(sigma_values):
        observed_value = observed_values[index]
        if not math.isfinite(observed_value):
            diagnostics.append(
                NeutronUncertaintyDiagnostic(
                    severity="error",
                    code="non_finite_observed",
                    message="observed intensity must be finite for neutron uncertainty checks.",
                    index=index,
                )
            )
        if not math.isfinite(value):
            diagnostics.append(
                NeutronUncertaintyDiagnostic(
                    severity="error",
                    code="non_finite_sigma",
                    message="sigma must be finite for neutron uncertainty checks.",
                    index=index,
                )
            )
            continue
        if value <= 0.0:
            diagnostics.append(
                NeutronUncertaintyDiagnostic(
                    severity="error",
                    code="non_positive_sigma",
                    message="sigma must be strictly positive for neutron weighting.",
                    index=index,
                )
            )
            continue
        if not math.isfinite(observed_value):
            continue
        floor = minimum * max(abs(observed_value), 1.0)
        if value < floor:
            diagnostics.append(
                NeutronUncertaintyDiagnostic(
                    severity="warning",
                    code="below_relative_sigma_floor",
                    message="sigma is below the configured relative uncertainty floor.",
                    index=index,
                )
            )
    return _result(len(observed_values), sigma_unit, minimum, diagnostics)


def _result(
    point_count: int,
    sigma_unit: str,
    minimum_relative_sigma: float,
    diagnostics: Sequence[NeutronUncertaintyDiagnostic],
) -> NeutronUncertaintyCheck:
    has_error = any(diagnostic.severity == "error" for diagnostic in diagnostics)
    has_warning = any(diagnostic.severity == "warning" for diagnostic in diagnostics)
    status = "error" if has_error else "warning" if has_warning else "ok"
    return NeutronUncertaintyCheck(
        status=status,
        point_count=point_count,
        sigma_unit=sigma_unit,
        minimum_relative_sigma=minimum_relative_sigma,
        diagnostics=tuple(diagnostics),
    )


def _number_sequence(values: Sequence[float], name: str) -> tuple[float, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of numbers.")
    return tuple(_number(value, f"{name}[{index}]") for index, value in enumerate(values))


def _number(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{name} must be a number, got {value!r}.")
    return float(value)


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _non_empty_string(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value.strip()
