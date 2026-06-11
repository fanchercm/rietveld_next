"""TOF detector-bank entities."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math

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

        object.__setattr__(self, "bank_id", bank_id)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "two_theta_degrees", two_theta)
        object.__setattr__(self, "sample_to_detector_m", distance)

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
        return payload


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
