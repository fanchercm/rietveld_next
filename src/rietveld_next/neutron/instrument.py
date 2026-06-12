"""Continuous-wave neutron instrument helpers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
import math

from rietveld_next.neutron.absorption import (
    WavelengthDependentAbsorptionHook,
    evaluate_absorption_transmission,
    validate_wavelength_angstrom,
)
from rietveld_next.neutron.corrections import (
    ExtinctionCorrectionHook,
    SampleGeometryCorrectionHook,
    evaluate_extinction_correction,
    evaluate_sample_geometry_correction,
)
from rietveld_next.neutron.scattering_lengths import (
    NeutronScatteringLength,
    lookup_bound_coherent_scattering_length,
)


@dataclass(frozen=True)
class NeutronScatterer:
    """Nuclear neutron scatterer contribution for a site or species.

    Args:
        isotope: Isotope or natural-element label accepted by
            :func:`lookup_bound_coherent_scattering_length`.
        occupancy: Unitless site occupancy on ``[0, 1]``.
        multiplicity: Positive integer site multiplicity.

    Raises:
        ValueError: If occupancy or multiplicity are invalid.
        KeyError: If the isotope is not in the current scattering-length table.

    Example:
        >>> NeutronScatterer("H-2").scattering_length.bound_coherent_fm
        6.671
    """

    isotope: str
    occupancy: float = 1.0
    multiplicity: int = 1
    scattering_length: NeutronScatteringLength = field(init=False)

    def __post_init__(self) -> None:
        """Validate scatterer metadata and normalize isotope lookup."""

        scattering_length = lookup_bound_coherent_scattering_length(self.isotope)
        occupancy = _finite_float(self.occupancy, "occupancy")
        if occupancy < 0.0 or occupancy > 1.0:
            raise ValueError(f"occupancy must be on [0, 1], got {occupancy!r}.")
        if isinstance(self.multiplicity, bool) or not isinstance(self.multiplicity, int):
            raise ValueError("multiplicity must be a positive integer.")
        if self.multiplicity <= 0:
            raise ValueError("multiplicity must be a positive integer.")
        object.__setattr__(self, "isotope", scattering_length.isotope)
        object.__setattr__(self, "occupancy", occupancy)
        object.__setattr__(self, "scattering_length", scattering_length)

    @property
    def weighted_scattering_length_fm(self) -> float:
        """Return occupancy- and multiplicity-weighted scattering length."""

        return self.multiplicity * self.occupancy * self.scattering_length.bound_coherent_fm

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible scatterer metadata."""

        return {
            "isotope": self.isotope,
            "occupancy": self.occupancy,
            "multiplicity": self.multiplicity,
            "scattering_length_fm": self.scattering_length.bound_coherent_fm,
        }


@dataclass(frozen=True)
class ContinuousWaveNeutronInstrument:
    """Small continuous-wave neutron instrument model.

    The model stores a fixed neutron wavelength and simple scalar instrument
    metadata. Nuclear scattering amplitudes are computed from bound coherent
    neutron scattering lengths in femtometers, not X-ray form factors.

    Args:
        wavelength_angstrom: Positive neutron wavelength in angstroms.
        zero_shift_degrees: Finite two-theta zero shift in degrees.
        intensity_scale: Non-negative dimensionless intensity scale.
        absorption_hook: Optional wavelength-dependent absorption hook. The
            hook is evaluated independently of profile kernels.
        sample_geometry_hook: Optional sample-geometry correction hook.
        extinction_hook: Optional extinction correction hook.

    Raises:
        ValueError: If wavelength, zero shift, scale, or hook metadata are
            invalid.

    Example:
        >>> instrument = ContinuousWaveNeutronInstrument(1.8)
        >>> round(instrument.bragg_two_theta_degrees(1.8), 6)
        60.0
    """

    wavelength_angstrom: float
    zero_shift_degrees: float = 0.0
    intensity_scale: float = 1.0
    absorption_hook: WavelengthDependentAbsorptionHook | None = None
    sample_geometry_hook: SampleGeometryCorrectionHook | None = None
    extinction_hook: ExtinctionCorrectionHook | None = None

    def __post_init__(self) -> None:
        """Validate continuous-wave neutron instrument metadata."""

        object.__setattr__(self, "wavelength_angstrom", validate_wavelength_angstrom(self.wavelength_angstrom))
        object.__setattr__(self, "zero_shift_degrees", _finite_float(self.zero_shift_degrees, "zero_shift_degrees"))
        scale = _finite_float(self.intensity_scale, "intensity_scale")
        if scale < 0.0:
            raise ValueError(f"intensity_scale must be non-negative, got {scale!r}.")
        object.__setattr__(self, "intensity_scale", scale)
        if self.absorption_hook is not None and not callable(
            getattr(self.absorption_hook, "transmission_factor", None)
        ):
            raise ValueError("absorption_hook must define transmission_factor(wavelength_angstrom).")
        if self.sample_geometry_hook is not None and not callable(
            getattr(self.sample_geometry_hook, "correction_factor", None)
        ):
            raise ValueError("sample_geometry_hook must define correction_factor(...).")
        if self.extinction_hook is not None and not callable(getattr(self.extinction_hook, "extinction_factor", None)):
            raise ValueError("extinction_hook must define extinction_factor(...).")

    def bragg_two_theta_degrees(self, d_spacing_angstrom: float, *, order: int = 1) -> float:
        """Compute CW neutron Bragg peak position in degrees two-theta.

        Args:
            d_spacing_angstrom: Positive lattice-plane spacing in angstroms.
            order: Positive diffraction order.

        Returns:
            Bragg two-theta in degrees after applying ``zero_shift_degrees``.

        Raises:
            ValueError: If inputs are invalid or the Bragg condition is
                unreachable.
        """

        d_spacing = _finite_float(d_spacing_angstrom, "d_spacing_angstrom")
        if d_spacing <= 0.0:
            raise ValueError(f"d_spacing_angstrom must be positive, got {d_spacing!r}.")
        if isinstance(order, bool) or not isinstance(order, int) or order <= 0:
            raise ValueError(f"order must be a positive integer, got {order!r}.")
        argument = order * self.wavelength_angstrom / (2.0 * d_spacing)
        if argument > 1.0:
            raise ValueError(
                "Bragg condition is unreachable: order * wavelength_angstrom "
                "must be less than or equal to 2 * d_spacing_angstrom."
            )
        return math.degrees(2.0 * math.asin(argument)) + self.zero_shift_degrees

    def scattering_length(self, isotope: str) -> NeutronScatteringLength:
        """Return bound coherent neutron scattering-length metadata."""

        return lookup_bound_coherent_scattering_length(isotope)

    def nuclear_amplitude_fm(self, scatterers: Sequence[NeutronScatterer]) -> float:
        """Return a synthetic nuclear scattering amplitude in femtometers.

        This helper intentionally computes only the occupancy- and
        multiplicity-weighted sum of bound coherent scattering lengths. Phase,
        Debye-Waller, magnetic, extinction, and geometry terms are outside this
        issue's scope.

        Args:
            scatterers: Sequence of neutron scatterer contributions.

        Returns:
            Weighted amplitude in femtometers. An empty sequence returns
            ``0.0``.

        Raises:
            ValueError: If ``scatterers`` is not a sequence of
                :class:`NeutronScatterer` instances.

        Example:
            >>> instrument = ContinuousWaveNeutronInstrument(1.8)
            >>> round(instrument.nuclear_amplitude_fm([NeutronScatterer("D")]), 3)
            6.671
        """

        if isinstance(scatterers, str) or not isinstance(scatterers, Sequence):
            raise ValueError("scatterers must be a sequence of NeutronScatterer instances.")
        amplitude = 0.0
        for index, scatterer in enumerate(scatterers):
            if not isinstance(scatterer, NeutronScatterer):
                raise ValueError(f"scatterers[{index}] must be a NeutronScatterer instance.")
            amplitude += scatterer.weighted_scattering_length_fm
        return amplitude

    def absorption_transmission(self, wavelength_angstrom: float | None = None) -> float:
        """Evaluate the attached absorption hook as a transmission factor."""

        wavelength = self.wavelength_angstrom if wavelength_angstrom is None else wavelength_angstrom
        return evaluate_absorption_transmission(self.absorption_hook, wavelength)

    def sample_geometry_correction(
        self,
        *,
        two_theta_degrees: float,
        wavelength_angstrom: float | None = None,
    ) -> float:
        """Evaluate the attached sample-geometry correction hook."""
        wavelength = self.wavelength_angstrom if wavelength_angstrom is None else wavelength_angstrom
        return evaluate_sample_geometry_correction(
            self.sample_geometry_hook,
            two_theta_degrees=two_theta_degrees,
            wavelength_angstrom=wavelength,
        )

    def extinction_correction(
        self,
        *,
        structure_factor_squared: float,
        wavelength_angstrom: float | None = None,
    ) -> float:
        """Evaluate the attached extinction correction hook."""
        wavelength = self.wavelength_angstrom if wavelength_angstrom is None else wavelength_angstrom
        return evaluate_extinction_correction(
            self.extinction_hook,
            structure_factor_squared=structure_factor_squared,
            wavelength_angstrom=wavelength,
        )

    def scale_intensity(
        self,
        intensity: float,
        wavelength_angstrom: float | None = None,
        *,
        two_theta_degrees: float | None = None,
        structure_factor_squared: float | None = None,
    ) -> float:
        """Apply instrument scale and optional absorption transmission.

        Args:
            intensity: Non-negative synthetic intensity.
            wavelength_angstrom: Optional wavelength override in angstroms for
                evaluating the absorption hook.
            two_theta_degrees: Required when a sample-geometry hook is present.
            structure_factor_squared: Required when an extinction hook is
                present.

        Returns:
            Scaled intensity. The calculation is deterministic and independent
            of profile-kernel evaluation.

        Raises:
            ValueError: If intensity, wavelength, or absorption transmission is
                invalid.
        """

        value = _finite_float(intensity, "intensity")
        if value < 0.0:
            raise ValueError(f"intensity must be non-negative, got {value!r}.")
        wavelength = self.wavelength_angstrom if wavelength_angstrom is None else wavelength_angstrom
        geometry = 1.0
        if self.sample_geometry_hook is not None:
            if two_theta_degrees is None:
                raise ValueError("two_theta_degrees is required when sample_geometry_hook is attached.")
            geometry = self.sample_geometry_correction(two_theta_degrees=two_theta_degrees, wavelength_angstrom=wavelength)
        extinction = 1.0
        if self.extinction_hook is not None:
            if structure_factor_squared is None:
                raise ValueError("structure_factor_squared is required when extinction_hook is attached.")
            extinction = self.extinction_correction(
                structure_factor_squared=structure_factor_squared,
                wavelength_angstrom=wavelength,
            )
        return value * self.intensity_scale * self.absorption_transmission(wavelength) * geometry * extinction

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible instrument metadata."""

        payload: dict[str, object] = {
            "instrument_type": "cw_neutron",
            "wavelength_angstrom": self.wavelength_angstrom,
            "zero_shift_degrees": self.zero_shift_degrees,
            "intensity_scale": self.intensity_scale,
            "absorption_hook": type(self.absorption_hook).__name__ if self.absorption_hook is not None else None,
        }
        if self.sample_geometry_hook is not None:
            payload["sample_geometry_hook"] = type(self.sample_geometry_hook).__name__
        if self.extinction_hook is not None:
            payload["extinction_hook"] = type(self.extinction_hook).__name__
        return payload


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)
