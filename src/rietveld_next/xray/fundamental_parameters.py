"""Fundamental-parameters X-ray profile skeletons and hook metadata.

These helpers define the first typed attachment points for continuous-wave
X-ray fundamental-parameters work. They are deterministic API skeletons for
profile plumbing; they do not implement a validated Cheary-Coelho convolution
or detector-specific instrument model.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math
from typing import Protocol

from rietveld_next.core.architecture import ApiStability, PluginCapability
from rietveld_next.diffraction.profiles import gaussian_profile
from rietveld_next.xray.wavelength import validate_wavelength_angstrom


class AxialDivergenceHook(Protocol):
    """Protocol for axial-divergence FWHM contributions.

    Implementations return a non-negative full width at half maximum in
    degrees two-theta for a finite ``0 < two_theta_degrees < 180`` position.

    Example:
        >>> hook = ConstantAxialDivergence(0.02)
        >>> hook.axial_fwhm_degrees(30.0)
        0.02
    """

    def axial_fwhm_degrees(self, two_theta_degrees: float) -> float:
        """Return an axial-divergence FWHM contribution in degrees."""


class DetectorResolutionHook(Protocol):
    """Protocol for detector-resolution FWHM contributions.

    Implementations return a non-negative full width at half maximum in
    degrees two-theta for a finite ``0 < two_theta_degrees < 180`` position.

    Example:
        >>> hook = ConstantDetectorResolution(0.03)
        >>> hook.detector_fwhm_degrees(30.0)
        0.03
    """

    def detector_fwhm_degrees(self, two_theta_degrees: float) -> float:
        """Return a detector-resolution FWHM contribution in degrees."""


@dataclass(frozen=True)
class EmissionLine:
    """Single X-ray emission-spectrum component.

    Args:
        label: Stable emission-line label, such as ``"Cu Kalpha1"``.
        wavelength_angstrom: Positive emission wavelength in angstroms.
        relative_intensity: Non-negative dimensionless line intensity.
        provenance: Optional source label for the wavelength/intensity values.

    Raises:
        ValueError: If label/provenance text is invalid, wavelength is not
            positive, or relative intensity is negative/non-finite.

    Example:
        >>> EmissionLine("Cu Kalpha1", 1.5406, 1.0).to_dict()["units"]["wavelength"]
        'angstrom'
    """

    label: str
    wavelength_angstrom: float
    relative_intensity: float = 1.0
    provenance: str | None = None

    def __post_init__(self) -> None:
        """Validate wavelength, intensity, and provenance metadata."""

        object.__setattr__(self, "label", _required_non_empty_string(self.label, "label"))
        object.__setattr__(self, "wavelength_angstrom", validate_wavelength_angstrom(self.wavelength_angstrom))
        intensity = _finite_float(self.relative_intensity, "relative_intensity")
        if intensity < 0.0:
            raise ValueError(f"relative_intensity must be non-negative, got {intensity!r}.")
        object.__setattr__(self, "relative_intensity", intensity)
        object.__setattr__(self, "provenance", _optional_non_empty_string(self.provenance, "provenance"))

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible line metadata."""

        payload: dict[str, object] = {
            "label": self.label,
            "wavelength_angstrom": self.wavelength_angstrom,
            "relative_intensity": self.relative_intensity,
            "units": {
                "wavelength": "angstrom",
                "relative_intensity": "dimensionless",
            },
        }
        if self.provenance is not None:
            payload["provenance"] = self.provenance
        return payload


@dataclass(frozen=True)
class EmissionSpectrum:
    """Validated X-ray emission spectrum.

    The relative intensities are stored as provided and normalized only during
    evaluation, so provenance and source table values remain auditable.

    Args:
        lines: One or more emission lines.
        reference_label: Optional line label used as the profile center
            reference. When omitted, the first line is the reference.

    Raises:
        ValueError: If no lines are provided, entries are not
            :class:`EmissionLine` instances, total intensity is zero, or the
            reference label is unknown.

    Example:
        >>> spectrum = EmissionSpectrum((EmissionLine("Cu Kalpha1", 1.5406),))
        >>> spectrum.reference_wavelength_angstrom
        1.5406
    """

    lines: tuple[EmissionLine, ...]
    reference_label: str | None = None

    def __post_init__(self) -> None:
        """Validate spectrum membership and normalize reference metadata."""

        if isinstance(self.lines, str) or not isinstance(self.lines, Sequence):
            raise ValueError("lines must be a non-empty sequence of EmissionLine instances.")
        lines = tuple(self.lines)
        if not lines:
            raise ValueError("lines must contain at least one EmissionLine.")
        for index, line in enumerate(lines):
            if not isinstance(line, EmissionLine):
                raise ValueError(f"lines[{index}] must be an EmissionLine instance.")
        total_intensity = sum(line.relative_intensity for line in lines)
        if total_intensity <= 0.0:
            raise ValueError("At least one emission line must have positive relative_intensity.")
        reference_label = _optional_non_empty_string(self.reference_label, "reference_label")
        if reference_label is not None and reference_label not in {line.label for line in lines}:
            raise ValueError(f"reference_label {reference_label!r} does not match an emission line label.")
        object.__setattr__(self, "lines", lines)
        object.__setattr__(self, "reference_label", reference_label)

    @property
    def reference_wavelength_angstrom(self) -> float:
        """Return the reference line wavelength in angstroms."""

        if self.reference_label is None:
            return self.lines[0].wavelength_angstrom
        for line in self.lines:
            if line.label == self.reference_label:
                return line.wavelength_angstrom
        raise ValueError(f"reference_label {self.reference_label!r} does not match an emission line label.")

    @property
    def weighted_wavelength_angstrom(self) -> float:
        """Return the relative-intensity-weighted wavelength in angstroms."""

        total_intensity = sum(line.relative_intensity for line in self.lines)
        return sum(line.wavelength_angstrom * line.relative_intensity for line in self.lines) / total_intensity

    def normalized_weights(self) -> tuple[float, ...]:
        """Return line intensity fractions in stored line order."""

        total_intensity = sum(line.relative_intensity for line in self.lines)
        return tuple(line.relative_intensity / total_intensity for line in self.lines)

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible spectrum metadata."""

        payload: dict[str, object] = {
            "lines": [line.to_dict() for line in self.lines],
            "reference_wavelength_angstrom": self.reference_wavelength_angstrom,
            "weighted_wavelength_angstrom": self.weighted_wavelength_angstrom,
            "units": {
                "wavelength": "angstrom",
                "relative_intensity": "dimensionless",
            },
        }
        if self.reference_label is not None:
            payload["reference_label"] = self.reference_label
        return payload


@dataclass(frozen=True)
class ConstantAxialDivergence:
    """Constant axial-divergence FWHM skeleton.

    This deterministic fixture is useful for testing hook composition. It is
    not a validated Soller-slit, specimen-length, or receiving-slit model.

    Args:
        fwhm_degrees: Non-negative FWHM contribution in degrees two-theta.

    Raises:
        ValueError: If ``fwhm_degrees`` is negative or non-finite.

    Example:
        >>> ConstantAxialDivergence(0.02).axial_fwhm_degrees(60.0)
        0.02
    """

    fwhm_degrees: float

    def __post_init__(self) -> None:
        """Validate the stored FWHM contribution."""

        object.__setattr__(self, "fwhm_degrees", _non_negative_degrees(self.fwhm_degrees, "fwhm_degrees"))

    def axial_fwhm_degrees(self, two_theta_degrees: float) -> float:
        """Return the constant axial FWHM after two-theta validation."""

        _validate_two_theta_degrees(two_theta_degrees)
        return self.fwhm_degrees


@dataclass(frozen=True)
class ConstantDetectorResolution:
    """Constant detector-resolution FWHM skeleton.

    This deterministic fixture is useful for testing detector hook plumbing. It
    is not a calibrated point-spread, strip-detector, or area-detector response.

    Args:
        fwhm_degrees: Non-negative FWHM contribution in degrees two-theta.

    Raises:
        ValueError: If ``fwhm_degrees`` is negative or non-finite.

    Example:
        >>> ConstantDetectorResolution(0.03).detector_fwhm_degrees(60.0)
        0.03
    """

    fwhm_degrees: float

    def __post_init__(self) -> None:
        """Validate the stored FWHM contribution."""

        object.__setattr__(self, "fwhm_degrees", _non_negative_degrees(self.fwhm_degrees, "fwhm_degrees"))

    def detector_fwhm_degrees(self, two_theta_degrees: float) -> float:
        """Return the constant detector FWHM after two-theta validation."""

        _validate_two_theta_degrees(two_theta_degrees)
        return self.fwhm_degrees


@dataclass(frozen=True)
class TwoDimensionalIntegrationMetadata:
    """Link from a 1D XRD profile to 2D integration provenance.

    Args:
        integration_id: Stable integration record identifier.
        source_image_uri: URI/path for the source detector image or image set.
        integrated_profile_uri: URI/path for the resulting 1D profile.
        azimuth_range_degrees: Inclusive lower/upper azimuth range in degrees.
            Values must be finite, ordered, bounded by ``[-360, 360]``, and span
            no more than 360 degrees.
        radial_axis_units: Unit identifier for the integrated radial axis.
        integration_software: Optional software/version label.
        provenance: Optional provenance note.

    Raises:
        ValueError: If identifiers, URIs, units, or azimuth bounds are invalid.

    Example:
        >>> metadata = TwoDimensionalIntegrationMetadata("int1", "images/raw.tif", "profiles/p.xy")
        >>> metadata.to_dict()["units"]["azimuth"]
        'degree'
    """

    integration_id: str
    source_image_uri: str
    integrated_profile_uri: str
    azimuth_range_degrees: tuple[float, float] = (-180.0, 180.0)
    radial_axis_units: str = "degree_two_theta"
    integration_software: str | None = None
    provenance: str | None = None

    def __post_init__(self) -> None:
        """Validate integration identity, URI links, units, and bounds."""

        object.__setattr__(self, "integration_id", _required_non_empty_string(self.integration_id, "integration_id"))
        object.__setattr__(self, "source_image_uri", _required_non_empty_string(self.source_image_uri, "source_image_uri"))
        object.__setattr__(
            self,
            "integrated_profile_uri",
            _required_non_empty_string(self.integrated_profile_uri, "integrated_profile_uri"),
        )
        object.__setattr__(
            self,
            "azimuth_range_degrees",
            _azimuth_range_degrees(self.azimuth_range_degrees),
        )
        object.__setattr__(self, "radial_axis_units", _required_non_empty_string(self.radial_axis_units, "radial_axis_units"))
        object.__setattr__(
            self,
            "integration_software",
            _optional_non_empty_string(self.integration_software, "integration_software"),
        )
        object.__setattr__(self, "provenance", _optional_non_empty_string(self.provenance, "provenance"))

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible integration metadata."""

        payload: dict[str, object] = {
            "integration_id": self.integration_id,
            "source_image_uri": self.source_image_uri,
            "integrated_profile_uri": self.integrated_profile_uri,
            "azimuth_range_degrees": list(self.azimuth_range_degrees),
            "radial_axis_units": self.radial_axis_units,
            "units": {
                "azimuth": "degree",
                "radial_axis": self.radial_axis_units,
            },
        }
        if self.integration_software is not None:
            payload["integration_software"] = self.integration_software
        if self.provenance is not None:
            payload["provenance"] = self.provenance
        return payload


@dataclass(frozen=True)
class FundamentalParametersProfileModel:
    """Small CW X-ray fundamental-parameters profile composition skeleton.

    The evaluator composes an emission spectrum, optional axial-divergence
    hook, optional detector-resolution hook, and optional 2D integration
    metadata link. It evaluates a sum of area-normalized Gaussian components
    and combines FWHM contributions in quadrature. This is a deterministic
    integration fixture, not a validated fundamental-parameters convolution.

    Args:
        emission_spectrum: Validated X-ray emission spectrum.
        base_gaussian_fwhm_degrees: Non-negative base Gaussian FWHM in degrees
            two-theta.
        axial_divergence_hook: Optional hook returning axial FWHM degrees.
        detector_resolution_hook: Optional hook returning detector FWHM degrees.
        integration_metadata: Optional 2D integration provenance link.

    Raises:
        ValueError: If metadata or hook interfaces are invalid.

    Example:
        >>> spectrum = EmissionSpectrum((EmissionLine("Cu Kalpha1", 1.5406),))
        >>> model = FundamentalParametersProfileModel(spectrum, base_gaussian_fwhm_degrees=0.1)
        >>> round(model.effective_fwhm_degrees(30.0), 3)
        0.1
    """

    emission_spectrum: EmissionSpectrum
    base_gaussian_fwhm_degrees: float
    axial_divergence_hook: AxialDivergenceHook | None = None
    detector_resolution_hook: DetectorResolutionHook | None = None
    integration_metadata: TwoDimensionalIntegrationMetadata | None = None

    def __post_init__(self) -> None:
        """Validate profile composition metadata and hook interfaces."""

        if not isinstance(self.emission_spectrum, EmissionSpectrum):
            raise ValueError("emission_spectrum must be an EmissionSpectrum instance.")
        object.__setattr__(
            self,
            "base_gaussian_fwhm_degrees",
            _non_negative_degrees(self.base_gaussian_fwhm_degrees, "base_gaussian_fwhm_degrees"),
        )
        if self.axial_divergence_hook is not None and not callable(
            getattr(self.axial_divergence_hook, "axial_fwhm_degrees", None)
        ):
            raise ValueError("axial_divergence_hook must define axial_fwhm_degrees(two_theta_degrees).")
        if self.detector_resolution_hook is not None and not callable(
            getattr(self.detector_resolution_hook, "detector_fwhm_degrees", None)
        ):
            raise ValueError("detector_resolution_hook must define detector_fwhm_degrees(two_theta_degrees).")
        if self.integration_metadata is not None and not isinstance(
            self.integration_metadata,
            TwoDimensionalIntegrationMetadata,
        ):
            raise ValueError("integration_metadata must be a TwoDimensionalIntegrationMetadata instance.")

    def effective_fwhm_degrees(self, two_theta_degrees: float) -> float:
        """Return quadrature-combined Gaussian FWHM in degrees two-theta."""

        two_theta = _validate_two_theta_degrees(two_theta_degrees)
        axial = evaluate_axial_divergence_fwhm(self.axial_divergence_hook, two_theta)
        detector = evaluate_detector_resolution_fwhm(self.detector_resolution_hook, two_theta)
        fwhm = math.sqrt(self.base_gaussian_fwhm_degrees**2 + axial**2 + detector**2)
        if fwhm <= 0.0:
            raise ValueError("effective FWHM must be positive; provide a base width or at least one hook contribution.")
        return fwhm

    def evaluate_profile(
        self,
        x_two_theta_degrees: Sequence[float],
        *,
        center_two_theta_degrees: float,
        area: float = 1.0,
    ) -> list[float]:
        """Evaluate the deterministic profile-composition skeleton.

        Args:
            x_two_theta_degrees: Axis positions in degrees two-theta.
            center_two_theta_degrees: Reference peak center in degrees
                two-theta for the spectrum reference line.
            area: Integrated area shared across emission lines according to
                their normalized relative intensities.

        Returns:
            Profile intensity values at each axis position.

        Raises:
            ValueError: If center, area, hook outputs, or axis values are
                invalid.
        """

        center = _validate_two_theta_degrees(center_two_theta_degrees)
        area_value = _finite_float(area, "area")
        values = [0.0 for _ in x_two_theta_degrees]
        reference_wavelength = self.emission_spectrum.reference_wavelength_angstrom
        for line, weight in zip(self.emission_spectrum.lines, self.emission_spectrum.normalized_weights(), strict=True):
            line_center = center * line.wavelength_angstrom / reference_wavelength
            line_fwhm = self.effective_fwhm_degrees(line_center)
            component = gaussian_profile(
                x_two_theta_degrees,
                center=line_center,
                fwhm=line_fwhm,
                area=area_value * weight,
            )
            values = [left + right for left, right in zip(values, component, strict=True)]
        return values

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible profile model metadata."""

        payload: dict[str, object] = {
            "model_type": "xray_fundamental_parameters_profile_skeleton",
            "emission_spectrum": self.emission_spectrum.to_dict(),
            "base_gaussian_fwhm_degrees": self.base_gaussian_fwhm_degrees,
            "axial_divergence_hook": (
                type(self.axial_divergence_hook).__name__ if self.axial_divergence_hook is not None else None
            ),
            "detector_resolution_hook": (
                type(self.detector_resolution_hook).__name__ if self.detector_resolution_hook is not None else None
            ),
            "units": {
                "two_theta": "degree",
                "fwhm": "degree",
                "area": "integrated_intensity",
            },
        }
        if self.integration_metadata is not None:
            payload["integration_metadata"] = self.integration_metadata.to_dict()
        return payload


def evaluate_axial_divergence_fwhm(
    hook: AxialDivergenceHook | None,
    two_theta_degrees: float,
) -> float:
    """Evaluate an optional axial-divergence hook.

    Args:
        hook: Axial-divergence hook or ``None``. ``None`` returns ``0.0``.
        two_theta_degrees: Peak position in degrees two-theta.

    Returns:
        Non-negative FWHM contribution in degrees two-theta.

    Raises:
        ValueError: If the hook interface or returned FWHM is invalid.

    Example:
        >>> evaluate_axial_divergence_fwhm(None, 30.0)
        0.0
    """

    two_theta = _validate_two_theta_degrees(two_theta_degrees)
    if hook is None:
        return 0.0
    evaluator = getattr(hook, "axial_fwhm_degrees", None)
    if not callable(evaluator):
        raise ValueError("axial divergence hook must define axial_fwhm_degrees(two_theta_degrees).")
    return _non_negative_degrees(evaluator(two_theta), "axial divergence FWHM")


def evaluate_detector_resolution_fwhm(
    hook: DetectorResolutionHook | None,
    two_theta_degrees: float,
) -> float:
    """Evaluate an optional detector-resolution hook.

    Args:
        hook: Detector-resolution hook or ``None``. ``None`` returns ``0.0``.
        two_theta_degrees: Peak position in degrees two-theta.

    Returns:
        Non-negative FWHM contribution in degrees two-theta.

    Raises:
        ValueError: If the hook interface or returned FWHM is invalid.

    Example:
        >>> evaluate_detector_resolution_fwhm(None, 30.0)
        0.0
    """

    two_theta = _validate_two_theta_degrees(two_theta_degrees)
    if hook is None:
        return 0.0
    evaluator = getattr(hook, "detector_fwhm_degrees", None)
    if not callable(evaluator):
        raise ValueError("detector resolution hook must define detector_fwhm_degrees(two_theta_degrees).")
    return _non_negative_degrees(evaluator(two_theta), "detector resolution FWHM")


def xray_fundamental_parameters_capabilities() -> tuple[PluginCapability, ...]:
    """Return capability declarations for the M17 X-ray hook skeletons.

    Returns:
        Deterministically ordered plugin capability metadata for the
        fundamental-parameters profile skeleton and attached hooks.

    Example:
        >>> xray_fundamental_parameters_capabilities()[0].name
        'xray.fundamental_parameters.profile_skeleton'
    """

    return (
        PluginCapability(
            name="xray.fundamental_parameters.profile_skeleton",
            version="0.1.0",
            supported_radiation_types=("lab_xray_cw", "synchrotron_xray_cw"),
            supported_axes=("two_theta",),
            parameter_names=(
                "axial_fwhm_degrees",
                "base_gaussian_fwhm_degrees",
                "detector_fwhm_degrees",
                "emission_relative_intensity",
                "integration_azimuth_range_degrees",
            ),
            units={
                "axial_fwhm_degrees": "degree",
                "base_gaussian_fwhm_degrees": "degree",
                "detector_fwhm_degrees": "degree",
                "emission_relative_intensity": "dimensionless",
                "integration_azimuth_range_degrees": "degree",
            },
            supports_derivatives=False,
            validation_functions=(
                "evaluate_axial_divergence_fwhm",
                "evaluate_detector_resolution_fwhm",
                "validate_wavelength_angstrom",
            ),
            stability=ApiStability.EXPERIMENTAL,
        ),
    )


def _azimuth_range_degrees(values: tuple[float, float]) -> tuple[float, float]:
    if isinstance(values, str) or not isinstance(values, Sequence) or len(values) != 2:
        raise ValueError("azimuth_range_degrees must contain exactly two finite degree values.")
    lower = _finite_float(values[0], "azimuth_range_degrees[0]")
    upper = _finite_float(values[1], "azimuth_range_degrees[1]")
    if lower < -360.0 or upper > 360.0:
        raise ValueError("azimuth_range_degrees values must stay within [-360, 360] degrees.")
    if lower >= upper:
        raise ValueError("azimuth_range_degrees lower bound must be less than upper bound.")
    if upper - lower > 360.0:
        raise ValueError("azimuth_range_degrees span must not exceed 360 degrees.")
    return (lower, upper)


def _validate_two_theta_degrees(two_theta_degrees: float) -> float:
    two_theta = _finite_float(two_theta_degrees, "two_theta_degrees")
    if two_theta <= 0.0 or two_theta >= 180.0:
        raise ValueError(f"two_theta_degrees must be greater than 0 and less than 180, got {two_theta!r}.")
    return two_theta


def _non_negative_degrees(value: float, name: str) -> float:
    width = _finite_float(value, name)
    if width < 0.0:
        raise ValueError(f"{name} must be non-negative, got {width!r}.")
    return width


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _required_non_empty_string(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required and must be a non-empty string.")
    return value


def _optional_non_empty_string(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string when supplied.")
    return value
