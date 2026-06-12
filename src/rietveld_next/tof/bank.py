"""TOF detector-bank entities."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math

from rietveld_next.optimization import residual_vector
from rietveld_next.tof.calibration import TimeOfFlightCalibrationParameters


@dataclass(frozen=True)
class TimeOfFlightDetectorBank:
    """Detector-bank metadata for TOF powder diffraction reductions.

    Args:
        bank_id: Stable non-empty detector-bank identifier.
        two_theta_degrees: Representative bank scattering angle in degrees.
            Values must be within the open interval ``(0, 180)``.
        detector_count: Positive number of detector elements represented by
            the bank.
        name: Optional human-readable bank label.
        sample_to_detector_m: Optional representative sample-to-detector
            distance in meters.
        calibration: Optional TOF calibration parameters for this bank.
        masked_bin_indices: Optional zero-based histogram-bin indices excluded
            from bank residual calculations.

    Raises:
        ValueError: If required identifiers, counts, geometry, or calibration
            linkage are invalid.

    Example:
        >>> bank = TimeOfFlightDetectorBank("bank-1", 145.0, 128)
        >>> bank.to_dict()["two_theta_degrees"]
        145.0
    """

    bank_id: str
    two_theta_degrees: float
    detector_count: int
    name: str | None = None
    sample_to_detector_m: float | None = None
    calibration: TimeOfFlightCalibrationParameters | None = None
    masked_bin_indices: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        """Validate detector-bank identity, geometry, and calibration link."""

        bank_id = _required_non_empty_string(self.bank_id, "bank_id")
        name = _optional_non_empty_string(self.name, "name")
        two_theta = _finite_float(self.two_theta_degrees, "two_theta_degrees")
        if two_theta <= 0.0 or two_theta >= 180.0:
            raise ValueError("two_theta_degrees must be greater than 0 and less than 180.")
        if isinstance(self.detector_count, bool) or not isinstance(self.detector_count, int):
            raise ValueError("detector_count must be an integer.")
        if self.detector_count <= 0:
            raise ValueError("detector_count must be positive.")
        distance = _optional_positive_float(self.sample_to_detector_m, "sample_to_detector_m")
        if self.calibration is not None and not isinstance(self.calibration, TimeOfFlightCalibrationParameters):
            raise ValueError("calibration must be a TimeOfFlightCalibrationParameters instance.")
        if (
            self.calibration is not None
            and self.calibration.bank_id is not None
            and self.calibration.bank_id != bank_id
        ):
            raise ValueError("calibration bank_id must match detector bank_id.")
        masked_bin_indices = _masked_bin_indices(self.masked_bin_indices)

        object.__setattr__(self, "bank_id", bank_id)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "two_theta_degrees", two_theta)
        object.__setattr__(self, "sample_to_detector_m", distance)
        object.__setattr__(self, "masked_bin_indices", masked_bin_indices)

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> TimeOfFlightDetectorBank:
        """Create a detector bank from a JSON-compatible mapping.

        Args:
            data: Mapping using the keys emitted by :meth:`to_dict`.

        Returns:
            Validated TOF detector-bank entity.

        Raises:
            ValueError: If required keys are missing or values are invalid.
        """

        if not isinstance(data, Mapping):
            raise ValueError("TimeOfFlightDetectorBank.from_dict data must be a mapping.")
        entity_type = data.get("entity_type")
        if entity_type not in (None, "tof_detector_bank"):
            raise ValueError("entity_type must be 'tof_detector_bank' when supplied.")
        for key in ("bank_id", "two_theta_degrees", "detector_count"):
            if key not in data:
                raise ValueError(f"{key} is required.")
        calibration_data = data.get("calibration")
        calibration = None
        if calibration_data is not None:
            if not isinstance(calibration_data, Mapping):
                raise ValueError("calibration must be a mapping when supplied.")
            calibration = TimeOfFlightCalibrationParameters.from_dict(calibration_data)
        return cls(
            bank_id=data["bank_id"],  # type: ignore[arg-type]
            two_theta_degrees=data["two_theta_degrees"],  # type: ignore[arg-type]
            detector_count=data["detector_count"],  # type: ignore[arg-type]
            name=data.get("name"),  # type: ignore[arg-type]
            sample_to_detector_m=data.get("sample_to_detector_m"),  # type: ignore[arg-type]
            calibration=calibration,
            masked_bin_indices=data.get("masked_bin_indices", ()),  # type: ignore[arg-type]
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible representation."""

        payload: dict[str, object] = {
            "entity_type": "tof_detector_bank",
            "bank_id": self.bank_id,
            "two_theta_degrees": self.two_theta_degrees,
            "detector_count": self.detector_count,
            "units": {
                "two_theta": "degree",
                "sample_to_detector": "meter",
            },
        }
        if self.name is not None:
            payload["name"] = self.name
        if self.sample_to_detector_m is not None:
            payload["sample_to_detector_m"] = self.sample_to_detector_m
        if self.calibration is not None:
            payload["calibration"] = self.calibration.to_dict()
        if self.masked_bin_indices:
            payload["masked_bin_indices"] = list(self.masked_bin_indices)
        return payload

    def unmasked_bin_indices(self, bin_count: int) -> tuple[int, ...]:
        """Return unmasked zero-based bin indices for a bank histogram.

        Args:
            bin_count: Number of histogram bins in the bank profile.

        Returns:
            Tuple of indices not listed in ``masked_bin_indices``.

        Raises:
            ValueError: If ``bin_count`` is invalid or any mask index is outside
                the histogram length.
        """

        count = _non_negative_int(bin_count, "bin_count")
        masked = _validated_mask_for_bin_count(self.masked_bin_indices, count)
        return tuple(index for index in range(count) if index not in masked)

    def apply_bin_mask(self, values: Sequence[float]) -> tuple[float, ...]:
        """Return sequence values with masked histogram bins removed.

        Args:
            values: Finite values in histogram-bin order.

        Returns:
            Values whose indices are not masked.

        Raises:
            ValueError: If values are invalid or a mask index is outside the
                value length.
        """

        finite_values = _finite_float_tuple(values, "values")
        return tuple(finite_values[index] for index in self.unmasked_bin_indices(len(finite_values)))

    def masked_residual_vector(
        self,
        observed: Sequence[float],
        calculated: Sequence[float],
        sigma: Sequence[float] | None = None,
    ) -> list[float]:
        """Compute residuals after propagating this bank's bin mask.

        The residual convention is inherited from
        :func:`rietveld_next.optimization.residual_vector`: observed minus
        calculated, optionally divided by positive standard uncertainty.

        Args:
            observed: Observed intensities in bank histogram-bin order.
            calculated: Calculated intensities in matching order.
            sigma: Optional positive standard uncertainties in matching order.

        Returns:
            Residual values for unmasked bins only.

        Raises:
            ValueError: If residual inputs are invalid or a mask index is outside
                the residual length.
        """

        residuals = residual_vector(observed, calculated, sigma)
        return list(self.apply_bin_mask(residuals))


def _required_non_empty_string(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value.strip()


def _optional_non_empty_string(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string when supplied.")
    return value.strip()


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _optional_positive_float(value: float | None, name: str) -> float | None:
    if value is None:
        return None
    number = _finite_float(value, name)
    if number <= 0.0:
        raise ValueError(f"{name} must be positive when supplied.")
    return number


def _non_negative_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer.")
    if value < 0:
        raise ValueError(f"{name} must be non-negative.")
    return value


def _masked_bin_indices(values: Sequence[int]) -> tuple[int, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError("masked_bin_indices must be a sequence of zero-based integer indices.")
    indices = []
    seen = set()
    for index, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"masked_bin_indices[{index}] must be an integer.")
        if value < 0:
            raise ValueError(f"masked_bin_indices[{index}] must be non-negative.")
        if value in seen:
            raise ValueError(f"masked_bin_indices must not contain duplicate index {value}.")
        seen.add(value)
        indices.append(value)
    return tuple(sorted(indices))


def _validated_mask_for_bin_count(masked_bin_indices: tuple[int, ...], bin_count: int) -> set[int]:
    out_of_range = [index for index in masked_bin_indices if index >= bin_count]
    if out_of_range:
        raise ValueError(
            "masked_bin_indices must be less than bin_count; "
            f"got {out_of_range[0]} for bin_count {bin_count}."
        )
    return set(masked_bin_indices)


def _finite_float_tuple(values: Sequence[float], name: str) -> tuple[float, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    return tuple(_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values))
