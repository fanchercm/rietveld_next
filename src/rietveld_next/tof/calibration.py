"""TOF calibration parameter sets and peak-position evaluation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math
from typing import ClassVar


@dataclass(frozen=True)
class TimeOfFlightCalibrationParameters:
    """DIFC/DIFA/zero calibration parameters for a TOF detector bank.

    Args:
        difc_microseconds_per_angstrom: Positive linear TOF calibration
            coefficient in microseconds per angstrom.
        difa_microseconds_per_angstrom_squared: Finite quadratic calibration
            coefficient in microseconds per angstrom squared.
        zero_microseconds: Finite additive zero offset in microseconds.
        bank_id: Optional detector-bank identifier this parameter set belongs
            to.
        d_spacing_range_angstrom: Optional positive increasing d-spacing range
            over which the parameters are considered calibrated.
        source: Optional provenance label for the calibration source.

    Raises:
        ValueError: If identifiers, units, finite values, or bounds are invalid.

    Example:
        >>> params = TimeOfFlightCalibrationParameters(18000.0, zero_microseconds=2.5)
        >>> params.parameter_vector()
        (18000.0, 0.0, 2.5)
        >>> params.peak_position_microseconds(1.25)
        22502.5
    """

    difc_microseconds_per_angstrom: float
    difa_microseconds_per_angstrom_squared: float = 0.0
    zero_microseconds: float = 0.0
    bank_id: str | None = None
    d_spacing_range_angstrom: tuple[float, float] | None = None
    source: str | None = None

    parameter_order: ClassVar[tuple[str, ...]] = (
        "difc_microseconds_per_angstrom",
        "difa_microseconds_per_angstrom_squared",
        "zero_microseconds",
    )

    def __post_init__(self) -> None:
        """Validate calibration parameters and normalize numeric values."""

        difc = _finite_float(self.difc_microseconds_per_angstrom, "difc_microseconds_per_angstrom")
        if difc <= 0.0:
            raise ValueError("difc_microseconds_per_angstrom must be positive.")
        difa = _finite_float(
            self.difa_microseconds_per_angstrom_squared,
            "difa_microseconds_per_angstrom_squared",
        )
        zero = _finite_float(self.zero_microseconds, "zero_microseconds")
        bank_id = _optional_non_empty_string(self.bank_id, "bank_id")
        source = _optional_non_empty_string(self.source, "source")
        d_range = _optional_d_spacing_range(self.d_spacing_range_angstrom)

        object.__setattr__(self, "difc_microseconds_per_angstrom", difc)
        object.__setattr__(self, "difa_microseconds_per_angstrom_squared", difa)
        object.__setattr__(self, "zero_microseconds", zero)
        object.__setattr__(self, "bank_id", bank_id)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "d_spacing_range_angstrom", d_range)

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> TimeOfFlightCalibrationParameters:
        """Create a calibration parameter set from a JSON-compatible mapping.

        Args:
            data: Mapping using the keys emitted by :meth:`to_dict`.

        Returns:
            Validated calibration parameter set.

        Raises:
            ValueError: If required keys are missing or values are invalid.
        """

        if not isinstance(data, Mapping):
            raise ValueError("TimeOfFlightCalibrationParameters.from_dict data must be a mapping.")
        calibration_type = data.get("calibration_type")
        if calibration_type not in (None, "tof_difc_difa_zero"):
            raise ValueError("calibration_type must be 'tof_difc_difa_zero' when supplied.")
        if "difc_microseconds_per_angstrom" not in data:
            raise ValueError("difc_microseconds_per_angstrom is required.")
        d_range = data.get("d_spacing_range_angstrom")
        return cls(
            difc_microseconds_per_angstrom=data["difc_microseconds_per_angstrom"],  # type: ignore[arg-type]
            difa_microseconds_per_angstrom_squared=data.get(
                "difa_microseconds_per_angstrom_squared",
                0.0,
            ),  # type: ignore[arg-type]
            zero_microseconds=data.get("zero_microseconds", 0.0),  # type: ignore[arg-type]
            bank_id=data.get("bank_id"),  # type: ignore[arg-type]
            d_spacing_range_angstrom=None
            if d_range is None
            else _sequence_pair(d_range, "d_spacing_range_angstrom"),
            source=data.get("source"),  # type: ignore[arg-type]
        )

    def parameter_vector(self) -> tuple[float, float, float]:
        """Return calibration values in deterministic DIFC, DIFA, zero order."""

        return (
            self.difc_microseconds_per_angstrom,
            self.difa_microseconds_per_angstrom_squared,
            self.zero_microseconds,
        )

    def peak_position_microseconds(self, d_spacing_angstrom: float) -> float:
        """Return the TOF peak center for one d-spacing.

        The deterministic DIFC-DIFA-zero model is:

        ```text
        tof_microseconds = DIFA * d^2 + DIFC * d + zero
        ```

        Args:
            d_spacing_angstrom: Positive d-spacing in angstrom.

        Returns:
            Peak center in microseconds.

        Raises:
            ValueError: If the d-spacing is non-finite, non-positive, outside
                the optional calibrated d-spacing range, or produces a
                non-positive TOF.
        """

        d_spacing = _positive_d_spacing(d_spacing_angstrom, "d_spacing_angstrom")
        self._validate_d_spacing_range(d_spacing)
        tof = (
            self.difa_microseconds_per_angstrom_squared * d_spacing * d_spacing
            + self.difc_microseconds_per_angstrom * d_spacing
            + self.zero_microseconds
        )
        if tof <= 0.0:
            raise ValueError(
                "DIFC-DIFA-zero calibration produced a non-positive peak position "
                f"for d_spacing_angstrom={d_spacing!r}."
            )
        return tof

    def peak_positions_microseconds(self, d_spacings_angstrom: Sequence[float]) -> tuple[float, ...]:
        """Return TOF peak centers for d-spacings in deterministic input order.

        Args:
            d_spacings_angstrom: Positive d-spacings in angstrom.

        Returns:
            Peak centers in microseconds.

        Raises:
            ValueError: If any d-spacing is invalid or outside calibrated bounds.
        """

        if isinstance(d_spacings_angstrom, str) or not isinstance(d_spacings_angstrom, Sequence):
            raise ValueError("d_spacings_angstrom must be a sequence of finite positive numbers.")
        return tuple(
            self.peak_position_microseconds(
                _positive_d_spacing(d_spacing, f"d_spacings_angstrom[{index}]")
            )
            for index, d_spacing in enumerate(d_spacings_angstrom)
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible representation."""

        payload: dict[str, object] = {
            "calibration_type": "tof_difc_difa_zero",
            "units": {
                "difc": "microsecond/angstrom",
                "difa": "microsecond/angstrom^2",
                "zero": "microsecond",
                "d_spacing_range": "angstrom",
            },
            "difc_microseconds_per_angstrom": self.difc_microseconds_per_angstrom,
            "difa_microseconds_per_angstrom_squared": self.difa_microseconds_per_angstrom_squared,
            "zero_microseconds": self.zero_microseconds,
        }
        if self.bank_id is not None:
            payload["bank_id"] = self.bank_id
        if self.d_spacing_range_angstrom is not None:
            payload["d_spacing_range_angstrom"] = list(self.d_spacing_range_angstrom)
        if self.source is not None:
            payload["source"] = self.source
        return payload

    def _validate_d_spacing_range(self, d_spacing_angstrom: float) -> None:
        if self.d_spacing_range_angstrom is None:
            return
        d_min, d_max = self.d_spacing_range_angstrom
        if d_spacing_angstrom < d_min or d_spacing_angstrom > d_max:
            raise ValueError(
                "d_spacing_angstrom must be within calibrated range "
                f"[{d_min}, {d_max}] angstrom, got {d_spacing_angstrom!r}."
            )


def _optional_d_spacing_range(values: tuple[float, float] | None) -> tuple[float, float] | None:
    if values is None:
        return None
    d_min, d_max = _sequence_pair(values, "d_spacing_range_angstrom")
    d_min = _finite_float(d_min, "d_spacing_range_angstrom[0]")
    d_max = _finite_float(d_max, "d_spacing_range_angstrom[1]")
    if d_min <= 0.0 or d_max <= 0.0:
        raise ValueError("d_spacing_range_angstrom values must be positive angstrom values.")
    if d_max <= d_min:
        raise ValueError("d_spacing_range_angstrom must be strictly increasing.")
    return (d_min, d_max)


def _sequence_pair(values: object, name: str) -> tuple[object, object]:
    if isinstance(values, str) or not isinstance(values, Sequence) or len(values) != 2:
        raise ValueError(f"{name} must contain exactly two values.")
    return (values[0], values[1])


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _positive_d_spacing(value: float, name: str) -> float:
    number = _finite_float(value, name)
    if number <= 0.0:
        raise ValueError(f"{name} must be a positive angstrom value.")
    return number


def _optional_non_empty_string(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string when supplied.")
    return value.strip()
