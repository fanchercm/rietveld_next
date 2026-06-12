"""Joint weighting helpers for neutron reduced datasets."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import math


_LIKELIHOOD_MODELS = frozenset({"independent_gaussian"})
_WEIGHTING_SCHEMES = frozenset({"inverse_variance", "unit"})


@dataclass(frozen=True)
class NeutronDatasetWeighting:
    """Weighting assumptions for one neutron dataset in a joint fit.

    Args:
        dataset_id: Stable dataset label.
        relative_weight: Positive dimensionless multiplier for the dataset.
        likelihood_model: Explicit likelihood assumption. The current
            implementation supports independent Gaussian residuals.
        weighting_scheme: ``"inverse_variance"`` or ``"unit"``.
        variance_scale: Positive dimensionless variance multiplier.
        assumptions: Additional audit notes recorded in deterministic order.

    Raises:
        ValueError: If labels, weights, likelihood, or scheme are invalid.

    Example:
        >>> model = NeutronDatasetWeighting("bank1")
        >>> model.weighted_residuals([5.0], [3.0], [2.0])
        (1.0,)
    """

    dataset_id: str
    relative_weight: float = 1.0
    likelihood_model: str = "independent_gaussian"
    weighting_scheme: str = "inverse_variance"
    variance_scale: float = 1.0
    assumptions: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate weighting assumptions."""

        relative_weight = _positive_float(self.relative_weight, "relative_weight")
        variance_scale = _positive_float(self.variance_scale, "variance_scale")
        likelihood = _non_empty_string(self.likelihood_model, "likelihood_model")
        scheme = _non_empty_string(self.weighting_scheme, "weighting_scheme")
        if likelihood not in _LIKELIHOOD_MODELS:
            raise ValueError(f"Unsupported likelihood_model {likelihood!r}.")
        if scheme not in _WEIGHTING_SCHEMES:
            raise ValueError(f"Unsupported weighting_scheme {scheme!r}.")
        notes = tuple(_non_empty_string(note, f"assumptions[{index}]") for index, note in enumerate(self.assumptions))
        object.__setattr__(self, "dataset_id", _non_empty_string(self.dataset_id, "dataset_id"))
        object.__setattr__(self, "relative_weight", relative_weight)
        object.__setattr__(self, "likelihood_model", likelihood)
        object.__setattr__(self, "weighting_scheme", scheme)
        object.__setattr__(self, "variance_scale", variance_scale)
        object.__setattr__(self, "assumptions", notes)

    def weighted_residuals(
        self,
        observed: Sequence[float],
        calculated: Sequence[float],
        sigma: Sequence[float] | None = None,
    ) -> tuple[float, ...]:
        """Return weighted residuals for this dataset.

        Args:
            observed: Observed reduced intensities.
            calculated: Calculated intensities with the same shape.
            sigma: Positive standard uncertainties for inverse-variance
                weighting.

        Returns:
            Tuple of weighted residuals using ``observed - calculated``.

        Raises:
            ValueError: If shapes, values, or required uncertainties are
                invalid.
        """

        observed_values = _finite_sequence(observed, "observed")
        calculated_values = _finite_sequence(calculated, "calculated")
        if len(observed_values) != len(calculated_values):
            raise ValueError("observed and calculated must have the same length.")
        if self.weighting_scheme == "inverse_variance":
            if sigma is None:
                raise ValueError("sigma is required for inverse_variance weighting.")
            sigma_values = _positive_sequence(sigma, "sigma")
            if len(sigma_values) != len(observed_values):
                raise ValueError("sigma must have the same length as observed.")
            factor = math.sqrt(self.relative_weight / self.variance_scale)
            return tuple(
                factor * (obs - calc) / sig
                for obs, calc, sig in zip(observed_values, calculated_values, sigma_values, strict=True)
            )
        factor = math.sqrt(self.relative_weight / self.variance_scale)
        return tuple(factor * (obs - calc) for obs, calc in zip(observed_values, calculated_values, strict=True))

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible weighting assumptions."""

        return {
            "dataset_id": self.dataset_id,
            "relative_weight": self.relative_weight,
            "likelihood_model": self.likelihood_model,
            "weighting_scheme": self.weighting_scheme,
            "variance_scale": self.variance_scale,
            "assumptions": list(self.assumptions),
        }


@dataclass(frozen=True)
class JointNeutronWeightingModel:
    """Ordered collection of neutron dataset weighting assumptions."""

    dataset_weightings: Sequence[NeutronDatasetWeighting]

    def __post_init__(self) -> None:
        """Validate non-empty, unique dataset weighting records."""

        if isinstance(self.dataset_weightings, str) or not isinstance(self.dataset_weightings, Sequence):
            raise ValueError("dataset_weightings must be a sequence of NeutronDatasetWeighting records.")
        records = tuple(self.dataset_weightings)
        if not records:
            raise ValueError("dataset_weightings cannot be empty.")
        seen: set[str] = set()
        for index, record in enumerate(records):
            if not isinstance(record, NeutronDatasetWeighting):
                raise ValueError(f"dataset_weightings[{index}] must be a NeutronDatasetWeighting record.")
            if record.dataset_id in seen:
                raise ValueError(f"Duplicate dataset_id {record.dataset_id!r}.")
            seen.add(record.dataset_id)
        object.__setattr__(self, "dataset_weightings", records)

    def combined_weighted_residuals(
        self,
        datasets: Mapping[str, Mapping[str, Sequence[float]]],
    ) -> tuple[float, ...]:
        """Return concatenated weighted residuals in model record order.

        Args:
            datasets: Mapping from dataset id to mappings containing
                ``observed``, ``calculated``, and optional ``sigma`` arrays.

        Returns:
            Concatenated weighted residual vector.

        Raises:
            ValueError: If any required dataset or array is missing.
        """

        if not isinstance(datasets, Mapping):
            raise ValueError("datasets must be a mapping keyed by dataset_id.")
        residuals: list[float] = []
        for record in self.dataset_weightings:
            dataset = datasets.get(record.dataset_id)
            if dataset is None:
                raise ValueError(f"Missing dataset {record.dataset_id!r}.")
            observed = _required_array(dataset, "observed")
            calculated = _required_array(dataset, "calculated")
            sigma = dataset.get("sigma")
            residuals.extend(record.weighted_residuals(observed, calculated, sigma))
        return tuple(residuals)

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible joint weighting metadata."""

        return {
            "model_type": "joint_neutron_weighting",
            "dataset_weightings": [record.to_dict() for record in self.dataset_weightings],
        }


def _required_array(dataset: Mapping[str, Sequence[float]], key: str) -> Sequence[float]:
    value = dataset.get(key)
    if value is None:
        raise ValueError(f"dataset must include {key!r}.")
    return value


def _positive_sequence(values: Sequence[float], name: str) -> tuple[float, ...]:
    sequence = _finite_sequence(values, name)
    for index, value in enumerate(sequence):
        if value <= 0.0:
            raise ValueError(f"{name}[{index}] must be positive, got {value!r}.")
    return sequence


def _finite_sequence(values: Sequence[float], name: str) -> tuple[float, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    return tuple(_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values))


def _positive_float(value: float, name: str) -> float:
    number = _finite_float(value, name)
    if number <= 0.0:
        raise ValueError(f"{name} must be positive, got {number!r}.")
    return number


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _non_empty_string(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value.strip()
