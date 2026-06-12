"""Runnable neutron validation examples."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math

from rietveld_next.neutron.instrument import ContinuousWaveNeutronInstrument, NeutronScatterer


@dataclass(frozen=True)
class NuclearNeutronValidationExample:
    """Synthetic nuclear neutron validation-example result."""

    status: str
    amplitude_fm: float
    expected_amplitude_fm: float
    intensity_fm_squared: float
    tolerance_fm: float
    assumptions: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible validation metadata."""

        return {
            "status": self.status,
            "amplitude_fm": self.amplitude_fm,
            "expected_amplitude_fm": self.expected_amplitude_fm,
            "intensity_fm_squared": self.intensity_fm_squared,
            "tolerance_fm": self.tolerance_fm,
            "assumptions": list(self.assumptions),
        }


def run_nuclear_neutron_validation_example(*, tolerance_fm: float = 1.0e-12) -> NuclearNeutronValidationExample:
    """Run a deterministic synthetic nuclear neutron validation example.

    The example computes an occupancy-weighted sum of bound coherent
    scattering lengths for a D2O-like synthetic composition:
    ``2 * b(2H) + b(nat O)``. It validates package plumbing against the table
    values already used by :class:`ContinuousWaveNeutronInstrument`; it is not
    a cross-software structure-factor benchmark.

    Args:
        tolerance_fm: Absolute femtometer tolerance for the analytic check.

    Returns:
        Validation result with assumptions and units.

    Raises:
        ValueError: If ``tolerance_fm`` is negative or non-finite.

    Example:
        >>> result = run_nuclear_neutron_validation_example()
        >>> result.status
        'passed'
    """

    if isinstance(tolerance_fm, bool) or not isinstance(tolerance_fm, int | float) or not math.isfinite(tolerance_fm):
        raise ValueError(f"tolerance_fm must be a finite number, got {tolerance_fm!r}.")
    if tolerance_fm < 0.0:
        raise ValueError("tolerance_fm must be non-negative.")
    instrument = ContinuousWaveNeutronInstrument(wavelength_angstrom=1.8)
    scatterers = [
        NeutronScatterer("D", multiplicity=2),
        NeutronScatterer("O"),
    ]
    amplitude = instrument.nuclear_amplitude_fm(scatterers)
    expected = 2.0 * 6.671 + 5.803
    status = "passed" if abs(amplitude - expected) <= tolerance_fm else "failed"
    return NuclearNeutronValidationExample(
        status=status,
        amplitude_fm=amplitude,
        expected_amplitude_fm=expected,
        intensity_fm_squared=amplitude * amplitude,
        tolerance_fm=tolerance_fm,
        assumptions=(
            "synthetic D2O-like composition",
            "bound coherent scattering lengths in femtometers",
            "no phase, Debye-Waller, absorption, extinction, or profile terms",
            "not a cross-software validation benchmark",
        ),
    )


def main() -> None:
    """Print the nuclear neutron validation example as JSON."""

    print(json.dumps(run_nuclear_neutron_validation_example().to_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
