"""TOF validation fixtures, diagnostics, and workflow specifications."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math
from typing import Any

from rietveld_next.tof.axis import TimeOfFlightHistogramAxis
from rietveld_next.tof.bank import TimeOfFlightDetectorBank
from rietveld_next.tof.calibration import TimeOfFlightCalibrationParameters
from rietveld_next.tof.profile import (
    TimeOfFlightBankBackground,
    TimeOfFlightBankObjectiveBlock,
    TimeOfFlightBankProfileParameters,
    TimeOfFlightReflection,
    assemble_multibank_objective,
)


@dataclass(frozen=True)
class TimeOfFlightSyntheticBenchmarkSpec:
    """Deterministic lightweight TOF synthetic benchmark workload.

    Args:
        bank_count: Number of synthetic detector banks.
        bins_per_bank: Number of histogram bins per bank.
        bin_width_microseconds: Positive uniform TOF bin width.
        d_spacings_angstrom: Positive reflection d-spacings included in every
            bank workload.
        residual_step: Deterministic observed-minus-calculated perturbation in
            intensity units.
        repeat_count: Number of objective evaluations performed by the smoke
            benchmark. This is a work counter, not a timing assertion.

    Raises:
        ValueError: If counts, units, or d-spacings are invalid.
    """

    bank_count: int = 2
    bins_per_bank: int = 9
    bin_width_microseconds: float = 10.0
    d_spacings_angstrom: tuple[float, ...] = (1.0,)
    residual_step: float = 0.05
    repeat_count: int = 2

    def __post_init__(self) -> None:
        """Validate benchmark workload shape and units."""

        object.__setattr__(self, "bank_count", _positive_int(self.bank_count, "bank_count"))
        bins = _positive_int(self.bins_per_bank, "bins_per_bank")
        if bins < 3:
            raise ValueError("bins_per_bank must be at least 3.")
        object.__setattr__(self, "bins_per_bank", bins)
        object.__setattr__(
            self,
            "bin_width_microseconds",
            _positive_float(self.bin_width_microseconds, "bin_width_microseconds"),
        )
        d_spacings = _positive_float_tuple(self.d_spacings_angstrom, "d_spacings_angstrom")
        if not d_spacings:
            raise ValueError("d_spacings_angstrom must contain at least one reflection.")
        object.__setattr__(self, "d_spacings_angstrom", d_spacings)
        object.__setattr__(self, "residual_step", _positive_float(self.residual_step, "residual_step"))
        object.__setattr__(self, "repeat_count", _positive_int(self.repeat_count, "repeat_count"))

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible benchmark specification."""

        return {
            "benchmark_type": "tof_synthetic_smoke",
            "bank_count": self.bank_count,
            "bins_per_bank": self.bins_per_bank,
            "bin_width_microseconds": self.bin_width_microseconds,
            "d_spacings_angstrom": list(self.d_spacings_angstrom),
            "residual_step": self.residual_step,
            "repeat_count": self.repeat_count,
        }


@dataclass(frozen=True)
class TimeOfFlightSyntheticBenchmarkResult:
    """Deterministic result summary for a TOF synthetic smoke benchmark."""

    spec: TimeOfFlightSyntheticBenchmarkSpec
    residual_count: int
    objective_value: float
    residual_checksum: float
    bank_labels: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible benchmark result."""

        return {
            "result_type": "tof_synthetic_smoke_result",
            "spec": self.spec.to_dict(),
            "residual_count": self.residual_count,
            "objective_value": self.objective_value,
            "residual_checksum": self.residual_checksum,
            "bank_labels": list(self.bank_labels),
        }


@dataclass(frozen=True)
class TimeOfFlightCalibrationWizardStep:
    """GUI calibration wizard step mapped to deterministic TOF API calls."""

    step_id: str
    title: str
    api_call: str
    required_inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    validation_note: str

    def __post_init__(self) -> None:
        """Validate wizard step metadata."""

        object.__setattr__(self, "step_id", _required_non_empty_string(self.step_id, "step_id"))
        object.__setattr__(self, "title", _required_non_empty_string(self.title, "title"))
        object.__setattr__(self, "api_call", _required_non_empty_string(self.api_call, "api_call"))
        object.__setattr__(
            self,
            "required_inputs",
            _non_empty_string_tuple(self.required_inputs, "required_inputs"),
        )
        object.__setattr__(self, "outputs", _non_empty_string_tuple(self.outputs, "outputs"))
        object.__setattr__(
            self,
            "validation_note",
            _required_non_empty_string(self.validation_note, "validation_note"),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible wizard step."""

        return {
            "step_id": self.step_id,
            "title": self.title,
            "api_call": self.api_call,
            "required_inputs": list(self.required_inputs),
            "outputs": list(self.outputs),
            "validation_note": self.validation_note,
        }


@dataclass(frozen=True)
class TimeOfFlightDiagnosticPlotData:
    """Serializable plot data for one TOF bank objective block."""

    bank_id: str
    tof_microseconds: tuple[float, ...]
    observed_intensity: tuple[float, ...]
    calculated_intensity: tuple[float, ...]
    difference_intensity: tuple[float, ...]
    objective_residuals: tuple[float, ...]
    unmasked_bin_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        """Validate diagnostic vector lengths and units."""

        bank_id = _required_non_empty_string(self.bank_id, "bank_id")
        tof = _positive_float_tuple(self.tof_microseconds, "tof_microseconds")
        observed = _finite_float_tuple(self.observed_intensity, "observed_intensity")
        calculated = _finite_float_tuple(self.calculated_intensity, "calculated_intensity")
        difference = _finite_float_tuple(self.difference_intensity, "difference_intensity")
        residuals = _finite_float_tuple(self.objective_residuals, "objective_residuals")
        active = _non_negative_int_tuple(self.unmasked_bin_indices, "unmasked_bin_indices")
        if not (len(tof) == len(observed) == len(calculated) == len(difference)):
            raise ValueError("tof, observed, calculated, and difference vectors must have matching lengths.")
        if len(residuals) != len(active):
            raise ValueError("objective_residuals length must match unmasked_bin_indices length.")
        object.__setattr__(self, "bank_id", bank_id)
        object.__setattr__(self, "tof_microseconds", tof)
        object.__setattr__(self, "observed_intensity", observed)
        object.__setattr__(self, "calculated_intensity", calculated)
        object.__setattr__(self, "difference_intensity", difference)
        object.__setattr__(self, "objective_residuals", residuals)
        object.__setattr__(self, "unmasked_bin_indices", active)

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible diagnostic plot data."""

        return {
            "data_type": "tof_diagnostic_plot_data",
            "bank_id": self.bank_id,
            "units": {
                "tof": "microsecond",
                "observed": "intensity",
                "calculated": "intensity",
                "difference": "intensity",
                "objective_residuals": "weighted_intensity",
            },
            "tof_microseconds": list(self.tof_microseconds),
            "observed_intensity": list(self.observed_intensity),
            "calculated_intensity": list(self.calculated_intensity),
            "difference_intensity": list(self.difference_intensity),
            "objective_residuals": list(self.objective_residuals),
            "unmasked_bin_indices": list(self.unmasked_bin_indices),
        }


@dataclass(frozen=True)
class TimeOfFlightEventModeProvenancePlaceholder:
    """Explicit placeholder for unsupported TOF event-mode reductions."""

    bank_id: str
    event_source: str
    reduction_state: str
    reason: str
    schema_version: int = 1
    supported: bool = False

    def __post_init__(self) -> None:
        """Validate event-mode provenance metadata."""

        object.__setattr__(self, "bank_id", _required_non_empty_string(self.bank_id, "bank_id"))
        object.__setattr__(self, "event_source", _required_non_empty_string(self.event_source, "event_source"))
        object.__setattr__(self, "reduction_state", _required_non_empty_string(self.reduction_state, "reduction_state"))
        object.__setattr__(self, "reason", _required_non_empty_string(self.reason, "reason"))
        object.__setattr__(self, "schema_version", _positive_int(self.schema_version, "schema_version"))
        if self.supported is not False:
            raise ValueError("TimeOfFlightEventModeProvenancePlaceholder.supported must be False.")

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible event-mode provenance."""

        return {
            "provenance_type": "tof_event_mode_placeholder",
            "schema_version": self.schema_version,
            "supported": False,
            "bank_id": self.bank_id,
            "event_source": self.event_source,
            "reduction_state": self.reduction_state,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class GsasIITimeOfFlightComparisonResult:
    """Comparison result for a synthetic GSAS-II TOF reference fixture."""

    passed: bool
    max_abs_error_microseconds: float
    tolerance_microseconds: float
    compared_peak_count: int

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible comparison result."""

        return {
            "passed": self.passed,
            "max_abs_error_microseconds": self.max_abs_error_microseconds,
            "tolerance_microseconds": self.tolerance_microseconds,
            "compared_peak_count": self.compared_peak_count,
        }


@dataclass(frozen=True)
class GsasIITimeOfFlightComparisonFixture:
    """Synthetic GSAS-II TOF comparison fixture with documented limitations."""

    fixture_id: str
    d_spacings_angstrom: tuple[float, ...]
    expected_tof_microseconds: tuple[float, ...]
    tolerance_microseconds: float
    reference: str = "GSAS-II synthetic DIFC/DIFA/zero fixture"
    limitations: tuple[str, ...] = (
        "Synthetic peak-center comparison only.",
        "No facility instrument profile or event-mode data are included.",
    )

    def __post_init__(self) -> None:
        """Validate reference fixture vectors and tolerance."""

        object.__setattr__(self, "fixture_id", _required_non_empty_string(self.fixture_id, "fixture_id"))
        d_spacings = _positive_float_tuple(self.d_spacings_angstrom, "d_spacings_angstrom")
        expected = _positive_float_tuple(self.expected_tof_microseconds, "expected_tof_microseconds")
        if len(d_spacings) != len(expected):
            raise ValueError("d_spacings_angstrom and expected_tof_microseconds lengths must match.")
        object.__setattr__(self, "d_spacings_angstrom", d_spacings)
        object.__setattr__(self, "expected_tof_microseconds", expected)
        object.__setattr__(
            self,
            "tolerance_microseconds",
            _positive_float(self.tolerance_microseconds, "tolerance_microseconds"),
        )
        object.__setattr__(self, "reference", _required_non_empty_string(self.reference, "reference"))
        object.__setattr__(self, "limitations", _non_empty_string_tuple(self.limitations, "limitations"))

    def compare(self, calculated_tof_microseconds: Sequence[float]) -> GsasIITimeOfFlightComparisonResult:
        """Compare calculated peak centers against the fixture.

        Args:
            calculated_tof_microseconds: Peak centers in microseconds in the
                same order as ``d_spacings_angstrom``.

        Returns:
            Maximum absolute error and pass/fail result.

        Raises:
            ValueError: If calculated vector length or values are invalid.
        """

        calculated = _positive_float_tuple(calculated_tof_microseconds, "calculated_tof_microseconds")
        if len(calculated) != len(self.expected_tof_microseconds):
            raise ValueError("calculated_tof_microseconds length must match fixture peak count.")
        errors = tuple(
            abs(actual - expected)
            for actual, expected in zip(calculated, self.expected_tof_microseconds, strict=True)
        )
        max_error = max(errors) if errors else 0.0
        return GsasIITimeOfFlightComparisonResult(
            passed=max_error <= self.tolerance_microseconds,
            max_abs_error_microseconds=max_error,
            tolerance_microseconds=self.tolerance_microseconds,
            compared_peak_count=len(calculated),
        )

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible comparison fixture metadata."""

        return {
            "fixture_type": "gsasii_tof_synthetic_peak_centers",
            "fixture_id": self.fixture_id,
            "reference": self.reference,
            "units": {
                "d_spacing": "angstrom",
                "tof": "microsecond",
                "tolerance": "microsecond",
            },
            "d_spacings_angstrom": list(self.d_spacings_angstrom),
            "expected_tof_microseconds": list(self.expected_tof_microseconds),
            "tolerance_microseconds": self.tolerance_microseconds,
            "limitations": list(self.limitations),
        }


def run_tof_synthetic_benchmark(
    spec: TimeOfFlightSyntheticBenchmarkSpec | None = None,
) -> TimeOfFlightSyntheticBenchmarkResult:
    """Run a deterministic lightweight TOF synthetic benchmark workload.

    Args:
        spec: Optional workload specification. Defaults to a small two-bank
            smoke fixture suitable for normal CI.

    Returns:
        Deterministic objective summary for the final repeated evaluation.
    """

    benchmark_spec = TimeOfFlightSyntheticBenchmarkSpec() if spec is None else spec
    if not isinstance(benchmark_spec, TimeOfFlightSyntheticBenchmarkSpec):
        raise ValueError("spec must be a TimeOfFlightSyntheticBenchmarkSpec instance.")
    blocks = _synthetic_objective_blocks(benchmark_spec)
    evaluation = None
    for _ in range(benchmark_spec.repeat_count):
        evaluation = assemble_multibank_objective(blocks, parameters=())
    if evaluation is None:
        raise ValueError("repeat_count must be positive.")
    return TimeOfFlightSyntheticBenchmarkResult(
        spec=benchmark_spec,
        residual_count=len(evaluation.residuals),
        objective_value=evaluation.objective_value,
        residual_checksum=sum((index + 1) * value for index, value in enumerate(evaluation.residuals)),
        bank_labels=tuple(
            block["label"]
            for block in evaluation.diagnostics.get("residual_blocks", ())
            if isinstance(block, Mapping)
        ),
    )


def tof_calibration_wizard_spec(
    bank_id: str,
    standard_d_spacings_angstrom: Sequence[float],
) -> tuple[TimeOfFlightCalibrationWizardStep, ...]:
    """Return GUI calibration wizard steps mapped to TOF API calls.

    Args:
        bank_id: Detector-bank identifier used in step labels.
        standard_d_spacings_angstrom: Positive calibration-standard d-spacings
            shown in the wizard.

    Returns:
        Ordered wizard step metadata for a GUI or workflow layer.
    """

    normalized_bank_id = _required_non_empty_string(bank_id, "bank_id")
    d_spacings = _positive_float_tuple(standard_d_spacings_angstrom, "standard_d_spacings_angstrom")
    if not d_spacings:
        raise ValueError("standard_d_spacings_angstrom must contain at least one d-spacing.")
    return (
        TimeOfFlightCalibrationWizardStep(
            step_id="load-axis",
            title=f"Load TOF axis for {normalized_bank_id}",
            api_call="TimeOfFlightHistogramAxis.from_centers",
            required_inputs=("centers_microseconds", "bin_width_microseconds", "bank_id"),
            outputs=("TimeOfFlightHistogramAxis",),
            validation_note="Centers and bin width must be positive microsecond values.",
        ),
        TimeOfFlightCalibrationWizardStep(
            step_id="define-bank",
            title=f"Define detector bank {normalized_bank_id}",
            api_call="TimeOfFlightDetectorBank",
            required_inputs=("bank_id", "two_theta_degrees", "detector_count"),
            outputs=("TimeOfFlightDetectorBank",),
            validation_note="Two-theta is in degrees and must be within the open interval (0, 180).",
        ),
        TimeOfFlightCalibrationWizardStep(
            step_id="fit-calibration",
            title="Fit DIFC/DIFA/zero parameters",
            api_call="TimeOfFlightCalibrationParameters",
            required_inputs=("difc_microseconds_per_angstrom", "difa_microseconds_per_angstrom_squared", "zero_microseconds"),
            outputs=("TimeOfFlightCalibrationParameters",),
            validation_note=f"{len(d_spacings)} positive standard d-spacings define the calibrated range.",
        ),
        TimeOfFlightCalibrationWizardStep(
            step_id="preview-centers",
            title="Preview calculated peak centers",
            api_call="TimeOfFlightCalibrationParameters.peak_positions_microseconds",
            required_inputs=("d_spacings_angstrom",),
            outputs=("tof_peak_centers_microseconds",),
            validation_note="Calculated centers must be positive and inside the histogram span.",
        ),
        TimeOfFlightCalibrationWizardStep(
            step_id="assemble-objective",
            title="Assemble bank objective",
            api_call="assemble_multibank_objective",
            required_inputs=("TimeOfFlightBankObjectiveBlock",),
            outputs=("ObjectiveEvaluation",),
            validation_note="Residual blocks are labeled by bank and masks are applied before objective assembly.",
        ),
    )


def tof_diagnostic_plot_data(block: TimeOfFlightBankObjectiveBlock) -> TimeOfFlightDiagnosticPlotData:
    """Build serializable diagnostic plot data for one TOF bank block."""

    if not isinstance(block, TimeOfFlightBankObjectiveBlock):
        raise ValueError("block must be a TimeOfFlightBankObjectiveBlock instance.")
    calculated = block.calculated_intensities()
    difference = tuple(
        observed - calculated_value
        for observed, calculated_value in zip(block.observed, calculated, strict=True)
    )
    return TimeOfFlightDiagnosticPlotData(
        bank_id=block.bank.bank_id,
        tof_microseconds=block.axis.centers_microseconds,
        observed_intensity=block.observed,
        calculated_intensity=calculated,
        difference_intensity=difference,
        objective_residuals=block.residuals(),
        unmasked_bin_indices=block.bank.unmasked_bin_indices(block.axis.bin_count),
    )


def event_mode_provenance_placeholder(
    bank_id: str,
    event_source: str,
    *,
    reduction_state: str = "not_reduced",
    reason: str = "Event-mode ingestion is not implemented in the current TOF foundation.",
) -> TimeOfFlightEventModeProvenancePlaceholder:
    """Return an explicit unsupported event-mode provenance placeholder."""

    return TimeOfFlightEventModeProvenancePlaceholder(
        bank_id=bank_id,
        event_source=event_source,
        reduction_state=reduction_state,
        reason=reason,
    )


def gsasii_tof_comparison_fixture(
    calibration: TimeOfFlightCalibrationParameters,
    d_spacings_angstrom: Sequence[float],
    *,
    fixture_id: str = "gsasii-synthetic-difc-difa-zero",
    tolerance_microseconds: float = 1.0e-9,
) -> GsasIITimeOfFlightComparisonFixture:
    """Create a synthetic GSAS-II TOF peak-center comparison fixture."""

    if not isinstance(calibration, TimeOfFlightCalibrationParameters):
        raise ValueError("calibration must be a TimeOfFlightCalibrationParameters instance.")
    d_spacings = _positive_float_tuple(d_spacings_angstrom, "d_spacings_angstrom")
    if not d_spacings:
        raise ValueError("d_spacings_angstrom must contain at least one d-spacing.")
    expected = calibration.peak_positions_microseconds(d_spacings)
    return GsasIITimeOfFlightComparisonFixture(
        fixture_id=fixture_id,
        d_spacings_angstrom=d_spacings,
        expected_tof_microseconds=expected,
        tolerance_microseconds=tolerance_microseconds,
    )


def _synthetic_objective_blocks(
    spec: TimeOfFlightSyntheticBenchmarkSpec,
) -> tuple[TimeOfFlightBankObjectiveBlock, ...]:
    blocks = []
    for bank_index in range(spec.bank_count):
        bank_id = f"bank-{bank_index + 1}"
        difc = 1000.0 + 125.0 * bank_index
        calibration = TimeOfFlightCalibrationParameters(
            difc_microseconds_per_angstrom=difc,
            difa_microseconds_per_angstrom_squared=0.0,
            zero_microseconds=0.0,
            bank_id=bank_id,
            d_spacing_range_angstrom=(min(spec.d_spacings_angstrom), max(spec.d_spacings_angstrom) + 0.1),
            source="M22 synthetic benchmark",
        )
        center = calibration.peak_position_microseconds(spec.d_spacings_angstrom[0])
        half_span = 0.5 * spec.bin_width_microseconds * (spec.bins_per_bank - 1)
        centers = tuple(
            center - half_span + spec.bin_width_microseconds * index
            for index in range(spec.bins_per_bank)
        )
        bank = TimeOfFlightDetectorBank(
            bank_id=bank_id,
            two_theta_degrees=145.0 - bank_index,
            detector_count=64 + bank_index,
            calibration=calibration,
        )
        axis = TimeOfFlightHistogramAxis.from_centers(
            centers,
            bin_width_microseconds=spec.bin_width_microseconds,
            bank_id=bank_id,
        )
        background = TimeOfFlightBankBackground(
            bank_id=bank_id,
            coefficients=(10.0 + bank_index, 0.01),
            origin_microseconds=center,
            scale_microseconds=spec.bin_width_microseconds,
        )
        profile = TimeOfFlightBankProfileParameters(
            bank_id=bank_id,
            alpha_inverse_microsecond=0.1,
            beta_inverse_microsecond=0.08,
            gaussian_fwhm_microseconds=spec.bin_width_microseconds,
            window_factor=3.0,
        )
        reflections = tuple(
            TimeOfFlightReflection(
                d_spacing_angstrom=d_spacing,
                intensity=20.0 / (reflection_index + 1),
                label=f"h{reflection_index}",
            )
            for reflection_index, d_spacing in enumerate(spec.d_spacings_angstrom)
        )
        seed_block = TimeOfFlightBankObjectiveBlock(
            bank=bank,
            axis=axis,
            observed=tuple(0.0 for _ in centers),
            background=background,
            profile_parameters=profile,
            reflections=reflections,
            sigma=tuple(1.0 for _ in centers),
        )
        calculated = seed_block.calculated_intensities()
        observed = tuple(
            value + spec.residual_step * ((index % 3) - 1)
            for index, value in enumerate(calculated)
        )
        blocks.append(
            TimeOfFlightBankObjectiveBlock(
                bank=bank,
                axis=axis,
                observed=observed,
                background=background,
                profile_parameters=profile,
                reflections=reflections,
                sigma=tuple(1.0 for _ in centers),
            )
        )
    return tuple(blocks)


def _required_non_empty_string(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value.strip()


def _positive_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer.")
    if value <= 0:
        raise ValueError(f"{name} must be positive.")
    return value


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _positive_float(value: float, name: str) -> float:
    number = _finite_float(value, name)
    if number <= 0.0:
        raise ValueError(f"{name} must be positive.")
    return number


def _finite_float_tuple(values: Sequence[float], name: str) -> tuple[float, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    return tuple(_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values))


def _positive_float_tuple(values: Sequence[float], name: str) -> tuple[float, ...]:
    numbers = _finite_float_tuple(values, name)
    for index, number in enumerate(numbers):
        if number <= 0.0:
            raise ValueError(f"{name}[{index}] must be positive.")
    return numbers


def _non_negative_int_tuple(values: Sequence[int], name: str) -> tuple[int, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of integer indices.")
    indices = []
    previous = -1
    for index, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name}[{index}] must be an integer.")
        if value < 0:
            raise ValueError(f"{name}[{index}] must be non-negative.")
        if value <= previous:
            raise ValueError(f"{name} must be strictly increasing.")
        indices.append(value)
        previous = value
    return tuple(indices)


def _non_empty_string_tuple(values: Sequence[str], name: str) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of non-empty strings.")
    strings = tuple(_required_non_empty_string(value, f"{name}[{index}]") for index, value in enumerate(values))
    if not strings:
        raise ValueError(f"{name} must contain at least one entry.")
    return strings
