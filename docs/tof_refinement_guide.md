# TOF Refinement Guide

## Purpose

This guide describes the current TOF metadata and calibration foundation for
contributors and agents.

## Scope

The current implementation provides TOF histogram axes, detector-bank metadata,
calibration parameter containers, DIFC-DIFA-zero peak-position evaluation,
bank-local histogram-bin masks for residual calculations, bank-specific
background/profile records, discretized back-to-back exponential profile
evaluation, reflection windowing, labeled multi-bank objective assembly,
validation smoke fixtures, diagnostic plot payloads, calibration wizard step
metadata, event-mode provenance placeholders, and synthetic GSAS-II peak-center
comparison fixtures. It supports typed deterministic records and
synthetic-profile validation, not facility-grade TOF refinement validation.

## Non-Goals

Facility-grade GSAS-II TOF comparison against external reference files,
event-mode reduction, and instrument-specific workflow diagnostics remain
future work.

## Example

Use `src/rietveld_next/tof/` helpers to define positive, increasing TOF bin
edges in microseconds and bank-specific calibration metadata before connecting
them to project histograms.

```python
from rietveld_next.tof import (
    TimeOfFlightBankBackground,
    TimeOfFlightBankObjectiveBlock,
    TimeOfFlightBankProfileParameters,
    TimeOfFlightCalibrationParameters,
    TimeOfFlightDetectorBank,
    TimeOfFlightHistogramAxis,
    TimeOfFlightReflection,
    assemble_multibank_objective,
    event_mode_provenance_placeholder,
    gsasii_tof_comparison_fixture,
    run_tof_synthetic_benchmark,
    tof_calibration_wizard_spec,
    tof_diagnostic_plot_data,
)

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

axis = TimeOfFlightHistogramAxis.from_centers(
    (26990.0, 27000.0, 27010.0),
    bin_width_microseconds=10.0,
    bank_id="bank-a",
)
block = TimeOfFlightBankObjectiveBlock(
    bank=bank,
    axis=axis,
    observed=(10.0, 21.0, 10.0),
    background=TimeOfFlightBankBackground(
        "bank-a",
        coefficients=(10.0,),
        origin_microseconds=27000.0,
        scale_microseconds=100.0,
    ),
    profile_parameters=TimeOfFlightBankProfileParameters(
        "bank-a",
        alpha_inverse_microsecond=0.1,
        beta_inverse_microsecond=0.08,
        gaussian_fwhm_microseconds=10.0,
    ),
    reflections=(TimeOfFlightReflection(d_spacing_angstrom=1.5, intensity=10.0),),
)
objective = assemble_multibank_objective((block,), parameters=())
diagnostics = tof_diagnostic_plot_data(block)
benchmark = run_tof_synthetic_benchmark()
wizard_steps = tof_calibration_wizard_spec("bank-a", (1.5,))
event_placeholder = event_mode_provenance_placeholder("bank-a", "events.nxs")
comparison_fixture = gsasii_tof_comparison_fixture(calibration, (1.5,))
comparison = comparison_fixture.compare(calibration.peak_positions_microseconds((1.5,)))
```

The peak-position convention is `tof_microseconds = DIFA * d^2 + DIFC * d +
zero`, with `d` in angstrom. Optional calibration bounds are inclusive and
reported in angstrom. `masked_bin_indices` are zero-based histogram-bin indices;
they are sorted for deterministic serialization and removed from residual
vectors after the standard `observed - calculated` residual calculation.

Bank backgrounds use polynomial coefficients in ascending power order on the
normalized coordinate `(tof_microseconds - origin_microseconds) /
scale_microseconds`. Profile parameters are bank-local and store `alpha` and
`beta` exponential coefficients in `1/microsecond` plus a Gaussian FWHM in
microseconds. The back-to-back exponential helper evaluates a discretized
Gaussian-core, two-sided exponential profile and normalizes over supplied bin
widths when used inside objective blocks. Reflection windows use the profile
window factor times the slowest decay length or Gaussian width and return
deterministic bin-index tuples.

`assemble_multibank_objective()` concatenates bank residual blocks in caller
order, applies each bank's mask through `TimeOfFlightDetectorBank`, and reports
diagnostic residual-block labels such as `tof:bank-a`. It does not currently
optimize or mutate shared phase parameters; callers pass the associated
parameter vector for objective reporting.

## M22 Validation and Workflow Helpers

`run_tof_synthetic_benchmark()` evaluates a deterministic two-bank smoke
workload by default. The result records the workload specification, residual
count, objective value, residual checksum, and bank labels. It is intended for
normal CI and does not assert wall-clock timing.

`tof_calibration_wizard_spec()` returns GUI/workflow steps mapped to concrete
API calls: axis loading, bank definition, DIFC/DIFA/zero calibration creation,
peak-center preview, and objective assembly. The spec records required inputs,
outputs, units, and validation notes so UI layers do not invent hidden
calibration behavior.

`tof_diagnostic_plot_data()` converts one `TimeOfFlightBankObjectiveBlock` into
serializable plot vectors for TOF centers, observed intensities, calculated
intensities, unweighted differences, objective residuals, and unmasked bin
indices. The payload preserves microsecond and intensity units.

`event_mode_provenance_placeholder()` records event-source provenance while
explicitly setting `supported=False`. It is a schema-stable placeholder for
future event-mode reduction, not an event-data reader.

`gsasii_tof_comparison_fixture()` creates a synthetic GSAS-II-labeled
DIFC/DIFA/zero peak-center fixture with microsecond tolerances and documented
limitations. It compares peak centers only and does not claim cross-software
validation against GSAS-II output files.

## Related Files

- [sections/06_tof_and_neutron_requirements.md](sections/06_tof_and_neutron_requirements.md)
- [validation_baseline.md](validation_baseline.md)
