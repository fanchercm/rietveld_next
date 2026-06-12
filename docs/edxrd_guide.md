# EDXRD Guide

## Purpose

This guide describes the current energy-dispersive X-ray diffraction foundation.

## Scope

The current EDXRD package stores positive energy axes in keV and provides a
linear or polynomial channel-to-energy calibration helper, a fixed-angle Bragg
conversion helper, a deterministic calibration workflow, a versioned import
template for channel/count spectra and calibration standards, a detector
response API for energy-domain stick peaks, high-pressure marker metadata,
an equation-of-state hook for synthetic compressed d-spacings, residual
diagnostics, and a lightweight synthetic benchmark workflow.

## Non-Goals

The detector response API is separated from crystallographic peak generation:
callers pass peak energies and integrated areas in counts. The startup response
helpers include an area-preserving Gaussian core, an optional one-sided
low-energy exponential tail hook, an optional fixed-energy escape peak hook,
and dead-time metadata recording. Detector-specific tail physics, pile-up,
nonlinearity, material-specific high-pressure refinement strategies, and
cross-software high-pressure validation remain future work.

## Example

Use EDXRD axis helpers to preserve channel/energy units, then record
calibration coefficients and fixed angle assumptions in project metadata and
validation reports.

```python
from rietveld_next.edxrd import (
    default_edxrd_import_template,
    fixed_angle_bragg_d_spacing_angstrom,
)

template = default_edxrd_import_template()
standard_rows = (
    {
        "channel": 0.0,
        "d_spacing_angstrom": fixed_angle_bragg_d_spacing_angstrom(10.0, 60.0),
        "label": "std-1",
    },
    {
        "channel": 2.0,
        "d_spacing_angstrom": fixed_angle_bragg_d_spacing_angstrom(11.0, 60.0),
        "label": "std-2",
    },
)
result = template.fit_calibration_from_standard_rows(
    standard_rows,
    two_theta_degrees=60.0,
    polynomial_order=1,
)
axis = result.to_axis(channel_count=2)
```

The fitted coefficients are ordered by ascending detector-channel power and use
the units `keV / channel^power`. Residuals are reported in keV. The workflow is
unweighted and deterministic, so callers must record any peak-picking,
standard-material, and fixed-angle provenance that was used before passing rows
to the helper.

The default import template requires tabular `channel` and `counts` columns,
accepts an optional non-negative `uncertainty` column, and validates separate
calibration-standard rows with `channel`, `d_spacing_angstrom`, and optional
`label` columns. Imported spectrum channels must be strictly increasing.

Use detector response helpers after crystallographic peak positions and areas
have already been computed:

```python
from rietveld_next.edxrd import (
    DetectorResponseModel,
    EDXRDResponsePeak,
    EnergyHistogramAxis,
    EscapePeakHook,
    GaussianDetectorResponse,
    LowEnergyTailHook,
)

axis = EnergyHistogramAxis(tuple(float(edge) for edge in range(1, 31)))
model = DetectorResponseModel(
    gaussian=GaussianDetectorResponse(fwhm_keV=0.25),
    low_energy_tail=LowEnergyTailHook(
        fraction=0.10,
        decay_keV=2.0,
        provenance={"assumption": "synthetic one-sided tail"},
    ),
    escape_peak=EscapePeakHook(
        escape_energy_keV=5.0,
        fraction=0.20,
        provenance={"detector_line": "synthetic escape"},
    ),
)
response = model.evaluate(
    axis,
    (EDXRDResponsePeak(energy_keV=20.0, area_counts=100.0, label="phase-peak-1"),),
)
```

Gaussian peak counts are integrated analytically over histogram bin edges. The
low-energy tail and escape-peak hooks are optional and record provenance in the
response result. Dead-time metadata records whether an upstream correction was
applied; it does not numerically correct counts.

## High-Pressure Synthetic Workflow

Use high-pressure marker records to attach pressure metadata to EDXRD spectra or
refinement steps. Pressure uses GPa, temperature uses K, and the marker records
the pressure standard, calibrant, uncertainty, and provenance.

```python
from rietveld_next.edxrd import (
    BirchMurnaghanEquationOfState,
    EquationOfStateHook,
    HighPressureMarker,
    fixed_angle_bragg_energy_keV,
)

marker = HighPressureMarker(
    "run-42",
    pressure_gpa=8.0,
    pressure_uncertainty_gpa=0.1,
    pressure_standard="synthetic ruby scale",
    calibrant="synthetic cubic standard",
    provenance={"source": "example"},
)
eos = BirchMurnaghanEquationOfState(
    reference_volume_angstrom3=64.0,
    bulk_modulus_gpa=180.0,
    bulk_modulus_derivative=4.0,
)
hook = EquationOfStateHook(
    eos=eos,
    reference_d_spacings_angstrom=(3.50, 3.05, 2.72),
    labels=("111", "200", "220"),
)
compressed_d = hook.compressed_d_spacings_angstrom(marker)
peak_energies = tuple(fixed_angle_bragg_energy_keV(d, 8.0) for d in compressed_d)
```

The equation-of-state hook uses third-order Birch-Murnaghan pressure and
isotropic d-spacing scaling from the volume ratio. It is a deterministic
startup hook for synthetic validation and documentation examples; it is not a
material-specific pressure refinement model.

Residual diagnostics use the `observed - calculated` convention:

```python
from rietveld_next.edxrd import EnergyHistogramAxis, compute_edxrd_residual_diagnostics

axis = EnergyHistogramAxis.from_linear_calibration(
    channel_count=3,
    offset_keV=24.0,
    gain_keV_per_channel=0.2,
)
diagnostics = compute_edxrd_residual_diagnostics(
    axis,
    observed_counts=(11.0, 18.0, 33.0),
    calculated_counts=(10.0, 20.0, 30.0),
    uncertainties_counts=(1.0, 2.0, 3.0),
    fitted_parameter_count=1,
)
```

The lightweight synthetic benchmark is opt-in and writes machine-readable JSON
only when the caller supplies an output path:

```python
from pathlib import Path

from rietveld_next.edxrd import write_edxrd_synthetic_benchmark_result

result = write_edxrd_synthetic_benchmark_result(
    Path("edxrd_m28_benchmark.json"),
    channel_count=64,
)
```

The benchmark fixture is deterministic and CPU-only. It records marker, EOS,
axis, peak-energy, residual-diagnostic, and assumption metadata in the result
environment, but it is not a cross-software validation claim.

## Related Files

- [sections/07_energy_dispersive_diffraction.md](sections/07_energy_dispersive_diffraction.md)
- [validation_baseline.md](validation_baseline.md)
