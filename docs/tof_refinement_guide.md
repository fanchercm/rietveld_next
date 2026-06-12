# TOF Refinement Guide

## Purpose

This guide describes the current TOF metadata and calibration foundation for
contributors and agents.

## Scope

The current implementation provides TOF histogram axes, detector-bank metadata,
calibration parameter containers, DIFC-DIFA-zero peak-position evaluation, and
bank-local histogram-bin masks for residual calculations. It supports typed
records and validation, not full TOF profile refinement.

## Non-Goals

Back-to-back exponential profile kernels, multi-bank objective assembly beyond
bank-local residual masking, and facility-grade GSAS-II TOF comparison fixtures
remain future work.

## Example

Use `src/rietveld_next/tof/` helpers to define positive, increasing TOF bin
edges in microseconds and bank-specific calibration metadata before connecting
them to project histograms.

```python
from rietveld_next.tof import TimeOfFlightCalibrationParameters, TimeOfFlightDetectorBank

calibration = TimeOfFlightCalibrationParameters(
    difc_microseconds_per_angstrom=18000.0,
    difa_microseconds_per_angstrom_squared=-2.0,
    zero_microseconds=4.5,
    bank_id="bank-a",
    d_spacing_range_angstrom=(0.5, 3.0),
)
center_microseconds = calibration.peak_position_microseconds(1.5)

bank = TimeOfFlightDetectorBank(
    "bank-a",
    two_theta_degrees=145.0,
    detector_count=128,
    calibration=calibration,
    masked_bin_indices=(1, 3),
)
residuals = bank.masked_residual_vector(
    observed=(10.0, 12.0, 9.5, 8.0),
    calculated=(9.0, 13.0, 9.0, 7.0),
    sigma=(2.0, 0.5, 0.25, 1.0),
)
```

The peak-position convention is `tof_microseconds = DIFA * d^2 + DIFC * d +
zero`, with `d` in angstrom. Optional calibration bounds are inclusive and
reported in angstrom. `masked_bin_indices` are zero-based histogram-bin indices;
they are sorted for deterministic serialization and removed from residual
vectors after the standard `observed - calculated` residual calculation.

## Related Files

- [sections/06_tof_and_neutron_requirements.md](sections/06_tof_and_neutron_requirements.md)
- [validation_baseline.md](validation_baseline.md)
