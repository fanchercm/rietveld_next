"""TOF bank-local profile models and multi-bank objective assembly."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math
from typing import Any

from rietveld_next.optimization.objectives import ObjectiveEvaluation, least_squares_evaluation
from rietveld_next.tof.axis import TimeOfFlightHistogramAxis
from rietveld_next.tof.bank import TimeOfFlightDetectorBank


@dataclass(frozen=True)
class TimeOfFlightBankBackground:
    """Bank-specific polynomial background model on a normalized TOF axis.

    Args:
        bank_id: Stable detector-bank identifier this background belongs to.
        coefficients: Polynomial coefficients in ascending power order.
        origin_microseconds: TOF origin used for the normalized coordinate.
        scale_microseconds: Positive TOF scale for the normalized coordinate.

    Raises:
        ValueError: If identifiers, coefficients, or coordinate metadata are
            invalid.

    Example:
        >>> background = TimeOfFlightBankBackground("bank-1", (10.0, 0.5), 1000.0, 100.0)
        >>> background.evaluate((1000.0, 1200.0))
        (10.0, 11.0)
    """

    bank_id: str
    coefficients: tuple[float, ...]
    origin_microseconds: float = 0.0
    scale_microseconds: float = 1.0

    def __post_init__(self) -> None:
        """Validate and normalize polynomial background fields."""

        bank_id = _required_non_empty_string(self.bank_id, "bank_id")
        coefficients = _finite_float_tuple(self.coefficients, "coefficients")
        if not coefficients:
            raise ValueError("coefficients must contain at least one value.")
        origin = _finite_float(self.origin_microseconds, "origin_microseconds")
        scale = _positive_float(self.scale_microseconds, "scale_microseconds")
        object.__setattr__(self, "bank_id", bank_id)
        object.__setattr__(self, "coefficients", coefficients)
        object.__setattr__(self, "origin_microseconds", origin)
        object.__setattr__(self, "scale_microseconds", scale)

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> TimeOfFlightBankBackground:
        """Create a background model from a JSON-compatible mapping."""

        if not isinstance(data, Mapping):
            raise ValueError("TimeOfFlightBankBackground.from_dict data must be a mapping.")
        model_type = data.get("model_type")
        if model_type not in (None, "tof_bank_polynomial_background"):
            raise ValueError("model_type must be 'tof_bank_polynomial_background' when supplied.")
        for key in ("bank_id", "coefficients"):
            if key not in data:
                raise ValueError(f"{key} is required.")
        return cls(
            bank_id=data["bank_id"],  # type: ignore[arg-type]
            coefficients=data["coefficients"],  # type: ignore[arg-type]
            origin_microseconds=data.get("origin_microseconds", 0.0),  # type: ignore[arg-type]
            scale_microseconds=data.get("scale_microseconds", 1.0),  # type: ignore[arg-type]
        )

    def evaluate(self, tof_microseconds: Sequence[float]) -> tuple[float, ...]:
        """Evaluate background intensities at TOF coordinates.

        Args:
            tof_microseconds: Finite TOF coordinates in microseconds.

        Returns:
            Background intensities in deterministic input order.
        """

        coordinates = _finite_float_tuple(tof_microseconds, "tof_microseconds")
        values: list[float] = []
        for tof in coordinates:
            x = (tof - self.origin_microseconds) / self.scale_microseconds
            value = 0.0
            for coefficient in reversed(self.coefficients):
                value = value * x + coefficient
            values.append(value)
        return tuple(values)

    def parameter_vector(self) -> tuple[float, ...]:
        """Return coefficients in deterministic ascending polynomial order."""

        return self.coefficients

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible representation."""

        return {
            "model_type": "tof_bank_polynomial_background",
            "bank_id": self.bank_id,
            "units": {
                "tof": "microsecond",
                "coefficients": "intensity",
            },
            "coefficients": list(self.coefficients),
            "origin_microseconds": self.origin_microseconds,
            "scale_microseconds": self.scale_microseconds,
        }


@dataclass(frozen=True)
class TimeOfFlightBankProfileParameters:
    """Bank-specific TOF peak-profile parameters.

    Args:
        bank_id: Stable detector-bank identifier this profile belongs to.
        alpha_inverse_microsecond: Positive low-TOF exponential decay
            coefficient.
        beta_inverse_microsecond: Positive high-TOF exponential decay
            coefficient.
        gaussian_fwhm_microseconds: Positive Gaussian full width at half
            maximum used for the local peak core.
        window_factor: Positive multiplier used to derive reflection windows
            from the slowest exponential decay length and Gaussian width.

    Raises:
        ValueError: If identifiers or numeric values are invalid.
    """

    bank_id: str
    alpha_inverse_microsecond: float
    beta_inverse_microsecond: float
    gaussian_fwhm_microseconds: float
    window_factor: float = 6.0

    def __post_init__(self) -> None:
        """Validate and normalize bank-specific profile parameters."""

        object.__setattr__(self, "bank_id", _required_non_empty_string(self.bank_id, "bank_id"))
        object.__setattr__(
            self,
            "alpha_inverse_microsecond",
            _positive_float(self.alpha_inverse_microsecond, "alpha_inverse_microsecond"),
        )
        object.__setattr__(
            self,
            "beta_inverse_microsecond",
            _positive_float(self.beta_inverse_microsecond, "beta_inverse_microsecond"),
        )
        object.__setattr__(
            self,
            "gaussian_fwhm_microseconds",
            _positive_float(self.gaussian_fwhm_microseconds, "gaussian_fwhm_microseconds"),
        )
        object.__setattr__(self, "window_factor", _positive_float(self.window_factor, "window_factor"))

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> TimeOfFlightBankProfileParameters:
        """Create profile parameters from a JSON-compatible mapping."""

        if not isinstance(data, Mapping):
            raise ValueError("TimeOfFlightBankProfileParameters.from_dict data must be a mapping.")
        model_type = data.get("model_type")
        if model_type not in (None, "tof_bank_back_to_back_exponential"):
            raise ValueError("model_type must be 'tof_bank_back_to_back_exponential' when supplied.")
        for key in (
            "bank_id",
            "alpha_inverse_microsecond",
            "beta_inverse_microsecond",
            "gaussian_fwhm_microseconds",
        ):
            if key not in data:
                raise ValueError(f"{key} is required.")
        return cls(
            bank_id=data["bank_id"],  # type: ignore[arg-type]
            alpha_inverse_microsecond=data["alpha_inverse_microsecond"],  # type: ignore[arg-type]
            beta_inverse_microsecond=data["beta_inverse_microsecond"],  # type: ignore[arg-type]
            gaussian_fwhm_microseconds=data["gaussian_fwhm_microseconds"],  # type: ignore[arg-type]
            window_factor=data.get("window_factor", 6.0),  # type: ignore[arg-type]
        )

    @property
    def gaussian_sigma_microseconds(self) -> float:
        """Return Gaussian sigma corresponding to the stored FWHM."""

        return self.gaussian_fwhm_microseconds / (2.0 * math.sqrt(2.0 * math.log(2.0)))

    @property
    def window_half_width_microseconds(self) -> float:
        """Return deterministic half-width used for reflection windowing."""

        slowest_decay = max(
            1.0 / self.alpha_inverse_microsecond,
            1.0 / self.beta_inverse_microsecond,
            self.gaussian_fwhm_microseconds,
        )
        return self.window_factor * slowest_decay

    def parameter_vector(self) -> tuple[float, float, float]:
        """Return profile values in deterministic alpha, beta, FWHM order."""

        return (
            self.alpha_inverse_microsecond,
            self.beta_inverse_microsecond,
            self.gaussian_fwhm_microseconds,
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible representation."""

        return {
            "model_type": "tof_bank_back_to_back_exponential",
            "bank_id": self.bank_id,
            "units": {
                "alpha": "1/microsecond",
                "beta": "1/microsecond",
                "gaussian_fwhm": "microsecond",
            },
            "alpha_inverse_microsecond": self.alpha_inverse_microsecond,
            "beta_inverse_microsecond": self.beta_inverse_microsecond,
            "gaussian_fwhm_microseconds": self.gaussian_fwhm_microseconds,
            "window_factor": self.window_factor,
        }


@dataclass(frozen=True)
class TimeOfFlightReflection:
    """Reflection contribution shared across TOF detector banks.

    Args:
        d_spacing_angstrom: Positive reflection d-spacing in angstrom.
        intensity: Finite integrated intensity in calculated intensity units.
        label: Optional deterministic reflection label.
    """

    d_spacing_angstrom: float
    intensity: float
    label: str = ""

    def __post_init__(self) -> None:
        """Validate reflection d-spacing and intensity."""

        object.__setattr__(self, "d_spacing_angstrom", _positive_float(self.d_spacing_angstrom, "d_spacing_angstrom"))
        intensity = _finite_float(self.intensity, "intensity")
        if intensity < 0.0:
            raise ValueError("intensity must be non-negative.")
        object.__setattr__(self, "intensity", intensity)
        object.__setattr__(self, "label", _optional_label(self.label, "label"))


@dataclass(frozen=True)
class TimeOfFlightReflectionWindow:
    """TOF bin window selected for one reflection on one detector bank."""

    bank_id: str
    center_microseconds: float
    lower_microseconds: float
    upper_microseconds: float
    bin_indices: tuple[int, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible representation."""

        return {
            "bank_id": self.bank_id,
            "center_microseconds": self.center_microseconds,
            "lower_microseconds": self.lower_microseconds,
            "upper_microseconds": self.upper_microseconds,
            "bin_indices": list(self.bin_indices),
        }


@dataclass(frozen=True)
class TimeOfFlightBankObjectiveBlock:
    """Inputs needed to calculate one bank-local residual block."""

    bank: TimeOfFlightDetectorBank
    axis: TimeOfFlightHistogramAxis
    observed: tuple[float, ...]
    background: TimeOfFlightBankBackground
    profile_parameters: TimeOfFlightBankProfileParameters
    reflections: tuple[TimeOfFlightReflection, ...]
    sigma: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        """Validate bank-local objective inputs and bank identifiers."""

        if not isinstance(self.bank, TimeOfFlightDetectorBank):
            raise ValueError("bank must be a TimeOfFlightDetectorBank instance.")
        if not isinstance(self.axis, TimeOfFlightHistogramAxis):
            raise ValueError("axis must be a TimeOfFlightHistogramAxis instance.")
        if self.axis.bank_id is not None and self.axis.bank_id != self.bank.bank_id:
            raise ValueError("axis bank_id must match bank.bank_id.")
        observed = _finite_float_tuple(self.observed, "observed")
        if len(observed) != self.axis.bin_count:
            raise ValueError("observed length must match the TOF axis bin_count.")
        if not isinstance(self.background, TimeOfFlightBankBackground):
            raise ValueError("background must be a TimeOfFlightBankBackground instance.")
        if self.background.bank_id != self.bank.bank_id:
            raise ValueError("background bank_id must match bank.bank_id.")
        if not isinstance(self.profile_parameters, TimeOfFlightBankProfileParameters):
            raise ValueError("profile_parameters must be a TimeOfFlightBankProfileParameters instance.")
        if self.profile_parameters.bank_id != self.bank.bank_id:
            raise ValueError("profile_parameters bank_id must match bank.bank_id.")
        reflections = _reflection_tuple(self.reflections)
        sigma = None if self.sigma is None else _finite_float_tuple(self.sigma, "sigma")
        if sigma is not None:
            if len(sigma) != len(observed):
                raise ValueError("sigma length must match observed length.")
            for index, sigma_value in enumerate(sigma):
                if sigma_value <= 0.0:
                    raise ValueError(f"sigma[{index}] must be positive.")
        object.__setattr__(self, "observed", observed)
        object.__setattr__(self, "reflections", reflections)
        object.__setattr__(self, "sigma", sigma)

    def calculated_intensities(self) -> tuple[float, ...]:
        """Return calculated bank intensities from background and reflections."""

        if self.bank.calibration is None:
            raise ValueError("bank calibration is required to calculate reflection centers.")
        centers = self.axis.centers_microseconds
        widths = self.axis.widths_microseconds
        calculated = list(self.background.evaluate(centers))
        for reflection in self.reflections:
            center = self.bank.calibration.peak_position_microseconds(reflection.d_spacing_angstrom)
            window = reflection_window(self.axis, self.profile_parameters, center)
            if not window.bin_indices:
                continue
            window_centers = tuple(centers[index] for index in window.bin_indices)
            window_widths = tuple(widths[index] for index in window.bin_indices)
            profile = back_to_back_exponential_profile(
                window_centers,
                center,
                self.profile_parameters,
                bin_widths_microseconds=window_widths,
                normalize=True,
            )
            for index, profile_value in zip(window.bin_indices, profile, strict=True):
                calculated[index] += reflection.intensity * profile_value * widths[index]
        return tuple(calculated)

    def residuals(self) -> tuple[float, ...]:
        """Return this bank's masked residual block."""

        return tuple(
            self.bank.masked_residual_vector(
                observed=self.observed,
                calculated=self.calculated_intensities(),
                sigma=self.sigma,
            )
        )

    def residual_label(self) -> str:
        """Return the deterministic label for this bank residual block."""

        return f"tof:{self.bank.bank_id}"


def back_to_back_exponential_profile(
    tof_microseconds: Sequence[float],
    center_microseconds: float,
    parameters: TimeOfFlightBankProfileParameters,
    *,
    bin_widths_microseconds: Sequence[float] | None = None,
    normalize: bool = True,
) -> tuple[float, ...]:
    """Evaluate a discretized TOF back-to-back exponential profile.

    The profile uses exponential low- and high-TOF tails multiplied by a
    Gaussian core. When ``normalize`` is true, the returned values are scaled so
    ``sum(profile_i * width_i) == 1`` for supplied widths, or
    ``sum(profile_i) == 1`` when widths are omitted.

    Args:
        tof_microseconds: TOF coordinates in microseconds.
        center_microseconds: Peak center in microseconds.
        parameters: Bank-local profile parameters.
        bin_widths_microseconds: Optional positive bin widths in microseconds.
        normalize: Whether to normalize the discrete profile.

    Returns:
        Profile values in deterministic input order.
    """

    if not isinstance(parameters, TimeOfFlightBankProfileParameters):
        raise ValueError("parameters must be a TimeOfFlightBankProfileParameters instance.")
    coordinates = _finite_float_tuple(tof_microseconds, "tof_microseconds")
    center = _positive_float(center_microseconds, "center_microseconds")
    if not coordinates:
        return ()
    widths = _optional_widths(bin_widths_microseconds, len(coordinates))
    sigma = parameters.gaussian_sigma_microseconds
    values: list[float] = []
    for tof in coordinates:
        delta = tof - center
        gaussian = math.exp(-0.5 * (delta / sigma) ** 2)
        tail = (
            math.exp(parameters.alpha_inverse_microsecond * delta)
            if delta < 0.0
            else math.exp(-parameters.beta_inverse_microsecond * delta)
        )
        values.append(gaussian * tail)
    if not normalize:
        return tuple(values)
    area = sum(value * width for value, width in zip(values, widths, strict=True))
    if area <= 0.0:
        raise ValueError("profile normalization area must be positive.")
    return tuple(value / area for value in values)


def reflection_window(
    axis: TimeOfFlightHistogramAxis,
    parameters: TimeOfFlightBankProfileParameters,
    center_microseconds: float,
) -> TimeOfFlightReflectionWindow:
    """Return bin indices within a profile-derived TOF reflection window."""

    if not isinstance(axis, TimeOfFlightHistogramAxis):
        raise ValueError("axis must be a TimeOfFlightHistogramAxis instance.")
    if not isinstance(parameters, TimeOfFlightBankProfileParameters):
        raise ValueError("parameters must be a TimeOfFlightBankProfileParameters instance.")
    if axis.bank_id is not None and axis.bank_id != parameters.bank_id:
        raise ValueError("axis bank_id must match profile parameter bank_id.")
    center = _positive_float(center_microseconds, "center_microseconds")
    half_width = parameters.window_half_width_microseconds
    lower = center - half_width
    upper = center + half_width
    indices = tuple(
        index
        for index, center_value in enumerate(axis.centers_microseconds)
        if lower <= center_value <= upper
    )
    return TimeOfFlightReflectionWindow(
        bank_id=parameters.bank_id,
        center_microseconds=center,
        lower_microseconds=lower,
        upper_microseconds=upper,
        bin_indices=indices,
    )


def assemble_multibank_objective(
    blocks: Sequence[TimeOfFlightBankObjectiveBlock],
    parameters: Sequence[float] = (),
) -> ObjectiveEvaluation:
    """Assemble a least-squares objective from labeled TOF bank residuals.

    Args:
        blocks: Bank-local objective blocks in deterministic residual order.
        parameters: Parameter vector associated with the objective evaluation.

    Returns:
        Objective evaluation whose diagnostics include bank residual labels and
        residual-block lengths.
    """

    block_tuple = _objective_block_tuple(blocks)
    residuals: list[float] = []
    residual_blocks: list[dict[str, Any]] = []
    for block in block_tuple:
        start = len(residuals)
        block_residuals = block.residuals()
        residuals.extend(block_residuals)
        residual_blocks.append(
            {
                "label": block.residual_label(),
                "bank_id": block.bank.bank_id,
                "start": start,
                "length": len(block_residuals),
            }
        )
    evaluation = least_squares_evaluation(parameters, residuals)
    diagnostics = dict(evaluation.diagnostics)
    diagnostics["residual_blocks"] = residual_blocks
    diagnostics["bank_count"] = len(block_tuple)
    return ObjectiveEvaluation(
        parameters=evaluation.parameters,
        objective_value=evaluation.objective_value,
        residuals=evaluation.residuals,
        diagnostics=diagnostics,
    )


def _required_non_empty_string(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value.strip()


def _optional_label(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string.")
    return value.strip()


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


def _optional_widths(values: Sequence[float] | None, expected_length: int) -> tuple[float, ...]:
    if values is None:
        return tuple(1.0 for _ in range(expected_length))
    widths = _finite_float_tuple(values, "bin_widths_microseconds")
    if len(widths) != expected_length:
        raise ValueError("bin_widths_microseconds length must match tof_microseconds length.")
    for index, width in enumerate(widths):
        if width <= 0.0:
            raise ValueError(f"bin_widths_microseconds[{index}] must be positive.")
    return widths


def _reflection_tuple(values: Sequence[TimeOfFlightReflection]) -> tuple[TimeOfFlightReflection, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError("reflections must be a sequence of TimeOfFlightReflection instances.")
    reflections = tuple(values)
    for index, reflection in enumerate(reflections):
        if not isinstance(reflection, TimeOfFlightReflection):
            raise ValueError(f"reflections[{index}] must be a TimeOfFlightReflection instance.")
    return reflections


def _objective_block_tuple(
    values: Sequence[TimeOfFlightBankObjectiveBlock],
) -> tuple[TimeOfFlightBankObjectiveBlock, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError("blocks must be a sequence of TimeOfFlightBankObjectiveBlock instances.")
    blocks = tuple(values)
    if not blocks:
        raise ValueError("blocks must contain at least one bank objective block.")
    seen: set[str] = set()
    for index, block in enumerate(blocks):
        if not isinstance(block, TimeOfFlightBankObjectiveBlock):
            raise ValueError(f"blocks[{index}] must be a TimeOfFlightBankObjectiveBlock instance.")
        if block.bank.bank_id in seen:
            raise ValueError(f"Duplicate bank objective block for bank_id {block.bank.bank_id!r}.")
        seen.add(block.bank.bank_id)
    return blocks
