"""Mantid reduced-data import adapter for neutron workflows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import math


@dataclass(frozen=True)
class MantidReducedDataset:
    """Dependency-free representation of a Mantid-style reduced workspace.

    Args:
        dataset_id: Stable dataset label.
        axis_values: Reduced scattering-axis centers.
        intensity_values: Reduced intensities.
        sigma_values: Optional positive standard uncertainties.
        axis_unit: Unit label for ``axis_values``.
        intensity_unit: Unit label for intensities and uncertainties.
        source: Provenance label for the import source.
        metadata: JSON-compatible adapter metadata.

    Raises:
        ValueError: If shapes, units, uncertainties, or metadata are invalid.
    """

    dataset_id: str
    axis_values: Sequence[float]
    intensity_values: Sequence[float]
    sigma_values: Sequence[float] | None = None
    axis_unit: str = "degrees_two_theta"
    intensity_unit: str = "counts"
    source: str = "mantid_reduced_workspace_mapping"
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and freeze reduced-dataset arrays."""

        axis = _finite_sequence(self.axis_values, "axis_values")
        intensity = _finite_sequence(self.intensity_values, "intensity_values")
        if len(axis) != len(intensity):
            raise ValueError("axis_values and intensity_values must have the same length.")
        if not axis:
            raise ValueError("axis_values and intensity_values cannot be empty.")
        for index in range(1, len(axis)):
            if axis[index] <= axis[index - 1]:
                raise ValueError("axis_values must be strictly increasing.")
        sigma = None
        if self.sigma_values is not None:
            sigma = _finite_sequence(self.sigma_values, "sigma_values")
            if len(sigma) != len(axis):
                raise ValueError("sigma_values must match axis_values length.")
            for index, value in enumerate(sigma):
                if value <= 0.0:
                    raise ValueError(f"sigma_values[{index}] must be positive, got {value!r}.")
        object.__setattr__(self, "dataset_id", _non_empty_string(self.dataset_id, "dataset_id"))
        object.__setattr__(self, "axis_values", axis)
        object.__setattr__(self, "intensity_values", intensity)
        object.__setattr__(self, "sigma_values", sigma)
        object.__setattr__(self, "axis_unit", _non_empty_string(self.axis_unit, "axis_unit"))
        object.__setattr__(self, "intensity_unit", _non_empty_string(self.intensity_unit, "intensity_unit"))
        object.__setattr__(self, "source", _non_empty_string(self.source, "source"))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def point_count(self) -> int:
        """Return the number of reduced data points."""

        return len(self.axis_values)

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible dataset metadata."""

        payload: dict[str, object] = {
            "dataset_id": self.dataset_id,
            "axis_values": list(self.axis_values),
            "intensity_values": list(self.intensity_values),
            "sigma_values": list(self.sigma_values) if self.sigma_values is not None else None,
            "axis_unit": self.axis_unit,
            "intensity_unit": self.intensity_unit,
            "source": self.source,
            "point_count": self.point_count,
            "metadata": dict(self.metadata),
        }
        return payload


def import_mantid_reduced_data(
    payload: Mapping[str, object],
    *,
    dataset_id: str = "mantid_reduced",
    axis_unit: str = "degrees_two_theta",
    intensity_unit: str = "counts",
    source: str = "mantid_reduced_workspace_mapping",
) -> MantidReducedDataset:
    """Import a documented Mantid reduced-data mapping shape.

    The supported shape mirrors a single reduced Mantid workspace spectrum:
    ``X`` is either length ``N`` point centers or length ``N + 1`` bin edges,
    while ``Y`` and optional ``E`` are length ``N`` intensities and standard
    uncertainties. Lower-case aliases ``x``, ``y``, and ``e`` are also
    accepted.

    Args:
        payload: Mapping containing ``X``/``Y`` and optional ``E`` arrays.
        dataset_id: Stable dataset label assigned to the imported record.
        axis_unit: Unit label for ``X`` centers.
        intensity_unit: Unit label for ``Y`` and ``E``.
        source: Provenance label for the adapter source.

    Returns:
        Validated reduced dataset with axis centers.

    Raises:
        ValueError: If required arrays are missing or shapes are unsupported.

    Example:
        >>> data = import_mantid_reduced_data({"X": [10.0, 20.0, 30.0], "Y": [5.0, 7.0]})
        >>> data.axis_values
        (15.0, 25.0)
    """

    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping containing X/Y arrays.")
    raw_x = _required_array(payload, ("X", "x", "DataX", "data_x"))
    raw_y = _required_array(payload, ("Y", "y", "DataY", "data_y"))
    raw_e = _optional_array(payload, ("E", "e", "DataE", "data_e", "sigma", "sigmas"))
    x_values = _finite_sequence(raw_x, "X")
    y_values = _finite_sequence(raw_y, "Y")
    if not y_values:
        raise ValueError("Y must contain at least one reduced intensity.")
    for index in range(1, len(x_values)):
        if x_values[index] <= x_values[index - 1]:
            raise ValueError("X must be strictly increasing.")
    if len(x_values) == len(y_values):
        axis_values = x_values
        x_shape = "point_centers"
    elif len(x_values) == len(y_values) + 1:
        axis_values = tuple(0.5 * (x_values[index] + x_values[index + 1]) for index in range(len(y_values)))
        x_shape = "bin_edges"
    else:
        raise ValueError("X must be length N point centers or length N + 1 bin edges for Y length N.")
    sigma_values = _finite_sequence(raw_e, "E") if raw_e is not None else None
    metadata = {
        "adapter": "mantid_reduced_data_v1",
        "x_shape": x_shape,
        "input_keys": sorted(str(key) for key in payload.keys()),
    }
    return MantidReducedDataset(
        dataset_id=dataset_id,
        axis_values=axis_values,
        intensity_values=y_values,
        sigma_values=sigma_values,
        axis_unit=axis_unit,
        intensity_unit=intensity_unit,
        source=source,
        metadata=metadata,
    )


def _required_array(payload: Mapping[str, object], keys: tuple[str, ...]) -> Sequence[float]:
    for key in keys:
        value = payload.get(key)
        if value is not None:
            if isinstance(value, str) or not isinstance(value, Sequence):
                raise ValueError(f"{key} must be a sequence of finite numbers.")
            return value
    expected = "/".join(keys)
    raise ValueError(f"payload must include {expected}.")


def _optional_array(payload: Mapping[str, object], keys: tuple[str, ...]) -> Sequence[float] | None:
    for key in keys:
        value = payload.get(key)
        if value is not None:
            if isinstance(value, str) or not isinstance(value, Sequence):
                raise ValueError(f"{key} must be a sequence of finite numbers.")
            return value
    return None


def _finite_sequence(values: Sequence[float], name: str) -> tuple[float, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    return tuple(_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values))


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _non_empty_string(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value.strip()
