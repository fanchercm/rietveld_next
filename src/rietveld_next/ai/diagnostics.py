"""Deterministic diagnostics for AI-mediated refinement workflows."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from statistics import mean, median
from types import MappingProxyType
from typing import Any, Mapping, Sequence


_SEVERITIES = {"info", "warning", "error"}


@dataclass(frozen=True)
class DiagnosticFinding:
    """A deterministic diagnostic finding for agent-visible reports.

    Args:
        code: Stable diagnostic code.
        severity: Severity label: ``info``, ``warning``, or ``error``.
        message: Human-readable diagnostic.
        value: Optional numeric value supporting the finding.
        unit: Unit for ``value`` when dimensional.
        parameter: Optional parameter name linked to the finding.

    Raises:
        ValueError: If required labels are invalid.
    """

    code: str
    severity: str
    message: str
    value: float | None = None
    unit: str | None = None
    parameter: str | None = None

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("DiagnosticFinding.code must be non-empty")
        if self.severity not in _SEVERITIES:
            raise ValueError("DiagnosticFinding.severity must be info, warning, or error")
        if not self.message:
            raise ValueError("DiagnosticFinding.message must be non-empty")
        if self.unit is not None and not self.unit:
            raise ValueError("DiagnosticFinding.unit must be non-empty when provided")
        if self.parameter is not None and not self.parameter:
            raise ValueError("DiagnosticFinding.parameter must be non-empty when provided")
        if self.value is not None:
            if not isfinite(float(self.value)):
                raise ValueError("DiagnosticFinding.value must be finite")
            object.__setattr__(self, "value", float(self.value))

    def to_payload(self) -> Mapping[str, Any]:
        """Return a deterministic JSON-like payload."""

        payload: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }
        if self.value is not None:
            payload["value"] = self.value
        if self.unit is not None:
            payload["unit"] = self.unit
        if self.parameter is not None:
            payload["parameter"] = self.parameter
        return MappingProxyType(payload)


@dataclass(frozen=True)
class ResidualPatternClassification:
    """Rule-based residual pattern classification skeleton."""

    labels: tuple[str, ...]
    confidence: float
    summary: Mapping[str, float]

    def __post_init__(self) -> None:
        if not self.labels:
            raise ValueError("ResidualPatternClassification.labels must be non-empty")
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("ResidualPatternClassification.confidence must be in [0, 1]")
        object.__setattr__(self, "summary", MappingProxyType(dict(self.summary)))

    def to_payload(self) -> Mapping[str, Any]:
        """Return a deterministic JSON-like payload."""

        return MappingProxyType(
            {
                "labels": self.labels,
                "confidence": self.confidence,
                "summary": dict(self.summary),
            }
        )


def diagnose_residuals(residuals: Sequence[float], *, unit: str = "count") -> Mapping[str, Any]:
    """Summarize residuals with deterministic diagnostics.

    Args:
        residuals: Observed-minus-calculated residual values.
        unit: Unit label for residual amplitudes.

    Returns:
        Summary statistics, pattern classification, and diagnostic findings.

    Raises:
        ValueError: If residuals are empty, non-finite, or unit is empty.
    """

    values = _finite_values("residuals", residuals)
    if not unit:
        raise ValueError("unit must be non-empty")
    classification = classify_residual_pattern(values)
    max_abs = max(abs(value) for value in values)
    findings = [
        DiagnosticFinding(
            code="residual_pattern",
            severity="info" if classification.labels == ("flat",) else "warning",
            message=f"Residual classifier labels: {', '.join(classification.labels)}.",
            value=classification.confidence,
        )
    ]
    if max_abs > 0.0 and abs(mean(values)) / max_abs > 0.25:
        findings.append(
            DiagnosticFinding(
                code="residual_bias",
                severity="warning",
                message="Residuals have a substantial signed bias relative to maximum amplitude.",
                value=mean(values),
                unit=unit,
            )
        )
    return MappingProxyType(
        {
            "count": len(values),
            "mean": mean(values),
            "median": median(values),
            "max_abs": max_abs,
            "pattern": classification.to_payload(),
            "diagnostics": tuple(finding.to_payload() for finding in findings),
        }
    )


def classify_residual_pattern(residuals: Sequence[float]) -> ResidualPatternClassification:
    """Classify simple residual patterns with deterministic rules.

    Args:
        residuals: Observed-minus-calculated residual values.

    Returns:
        A skeleton classification suitable for agent reports and future model
        replacement. Labels are rule-derived and do not claim learned accuracy.

    Raises:
        ValueError: If residuals are empty or non-finite.
    """

    values = _finite_values("residuals", residuals)
    max_abs = max(abs(value) for value in values)
    avg = mean(values)
    abs_values = [abs(value) for value in values]
    median_abs = median(abs_values)
    sign_changes = _sign_change_fraction(values)
    labels: list[str] = []

    if max_abs == 0.0:
        labels.append("flat")
    if max_abs > 0.0 and abs(avg) / max_abs >= 0.25:
        labels.append("positive_bias" if avg > 0.0 else "negative_bias")
    if len(values) >= 4 and sign_changes >= 0.65:
        labels.append("alternating")
    if median_abs > 0.0 and max_abs / median_abs >= 4.0:
        labels.append("spike")
    if len(values) >= 6 and abs(mean(values[: len(values) // 2]) - mean(values[len(values) // 2 :])) > 0.35 * max_abs:
        labels.append("drift")
    if not labels:
        labels.append("unclassified")

    confidence = min(1.0, 0.35 + 0.15 * len(labels) + min(0.25, sign_changes * 0.25))
    return ResidualPatternClassification(
        labels=tuple(labels),
        confidence=round(confidence, 6),
        summary=MappingProxyType(
            {
                "mean": avg,
                "max_abs": max_abs,
                "median_abs": median_abs,
                "sign_change_fraction": sign_changes,
            }
        ),
    )


def detect_nonphysical_solution(parameters: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    """Detect common nonphysical parameter states.

    Args:
        parameters: Mapping from parameter name to either a numeric value or a
            mapping containing ``value`` and optional bounds/unit metadata.

    Returns:
        Stable finding payloads. The detector is conservative and rule-based.

    Raises:
        TypeError: If parameters is not a mapping.
        ValueError: If parameter values are non-finite.
    """

    if not isinstance(parameters, Mapping):
        raise TypeError("parameters must be a mapping")
    findings: list[DiagnosticFinding] = []
    for name in sorted(parameters):
        value, lower, upper, unit = _parameter_parts(name, parameters[name])
        lowered = name.lower()
        if lower is not None and value < lower:
            findings.append(_parameter_finding("below_bound", name, value, unit, f"Parameter `{name}` is below bound."))
        if upper is not None and value > upper:
            findings.append(_parameter_finding("above_bound", name, value, unit, f"Parameter `{name}` is above bound."))
        if any(token in lowered for token in ("scale", "phase_fraction", "occupancy", "occ")) and value < 0.0:
            findings.append(_parameter_finding("negative_amount", name, value, unit, f"Parameter `{name}` must not be negative."))
        if any(token in lowered for token in ("occupancy", "occ", "phase_fraction")) and value > 1.0:
            findings.append(_parameter_finding("fraction_gt_one", name, value, unit, f"Parameter `{name}` exceeds 1.0."))
        if any(token in lowered for token in ("uiso", "biso", "adp")) and value < 0.0:
            findings.append(_parameter_finding("negative_displacement", name, value, unit, f"Displacement parameter `{name}` is negative."))
    return tuple(finding.to_payload() for finding in findings)


def detect_overfitting(
    *,
    train_rwp: float,
    validation_rwp: float,
    parameter_count: int,
    observation_count: int,
    previous_validation_rwp: float | None = None,
) -> tuple[Mapping[str, Any], ...]:
    """Detect simple overfitting indicators from refinement metrics.

    Args:
        train_rwp: Rwp or equivalent metric on fitted observations.
        validation_rwp: Rwp or equivalent metric on held-out observations.
        parameter_count: Number of refined parameters.
        observation_count: Number of observations contributing to the fit.
        previous_validation_rwp: Previous validation metric for regression checks.

    Returns:
        Stable finding payloads.

    Raises:
        ValueError: If metrics are non-finite or counts are invalid.
    """

    train = _finite_float("train_rwp", train_rwp)
    validation = _finite_float("validation_rwp", validation_rwp)
    if train < 0.0 or validation < 0.0:
        raise ValueError("Rwp metrics must be non-negative")
    if parameter_count < 0:
        raise ValueError("parameter_count must be non-negative")
    if observation_count <= 0:
        raise ValueError("observation_count must be positive")
    findings: list[DiagnosticFinding] = []
    ratio = parameter_count / observation_count
    if ratio > 0.2:
        findings.append(
            DiagnosticFinding(
                code="high_parameter_density",
                severity="warning",
                message="Parameter count is high relative to observations.",
                value=ratio,
            )
        )
    if train > 0.0 and (validation - train) / train > 0.25:
        findings.append(
            DiagnosticFinding(
                code="validation_gap",
                severity="warning",
                message="Validation metric is substantially worse than fitted metric.",
                value=(validation - train) / train,
            )
        )
    if previous_validation_rwp is not None:
        previous = _finite_float("previous_validation_rwp", previous_validation_rwp)
        if validation > previous:
            findings.append(
                DiagnosticFinding(
                    code="validation_regression",
                    severity="warning",
                    message="Validation metric worsened after the latest refinement step.",
                    value=validation - previous,
                )
            )
    return tuple(finding.to_payload() for finding in findings)


def _parameter_finding(code: str, name: str, value: float, unit: str | None, message: str) -> DiagnosticFinding:
    return DiagnosticFinding(code=code, severity="error", message=message, value=value, unit=unit, parameter=name)


def _parameter_parts(name: str, raw: Any) -> tuple[float, float | None, float | None, str | None]:
    if not name:
        raise ValueError("parameter names must be non-empty")
    if isinstance(raw, Mapping):
        if "value" not in raw:
            raise ValueError(f"parameter `{name}` mapping must include value")
        value = _finite_float(name, raw["value"])
        lower = None if raw.get("lower_bound") is None else _finite_float(f"{name}.lower_bound", raw["lower_bound"])
        upper = None if raw.get("upper_bound") is None else _finite_float(f"{name}.upper_bound", raw["upper_bound"])
        unit = raw.get("unit")
        if unit is not None and not isinstance(unit, str):
            raise TypeError(f"parameter `{name}` unit must be a string")
        if unit == "":
            raise ValueError(f"parameter `{name}` unit must be non-empty")
        if lower is not None and upper is not None and lower > upper:
            raise ValueError(f"parameter `{name}` lower_bound cannot exceed upper_bound")
        return value, lower, upper, unit
    return _finite_float(name, raw), None, None, None


def _finite_values(label: str, values: Sequence[float]) -> tuple[float, ...]:
    if not values:
        raise ValueError(f"{label} must be non-empty")
    return tuple(_finite_float(label, value) for value in values)


def _finite_float(label: str, value: Any) -> float:
    converted = float(value)
    if not isfinite(converted):
        raise ValueError(f"{label} must contain only finite values")
    return converted


def _sign_change_fraction(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    changes = 0
    previous = 0
    compared = 0
    for value in values:
        sign = 1 if value > 0.0 else -1 if value < 0.0 else 0
        if sign == 0:
            continue
        if previous != 0:
            compared += 1
            if sign != previous:
                changes += 1
        previous = sign
    if compared == 0:
        return 0.0
    return changes / compared
