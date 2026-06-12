# EDXRD Guide

## Purpose

This guide describes the current energy-dispersive X-ray diffraction foundation.

## Scope

The current EDXRD package stores positive energy axes in keV and provides a
linear or polynomial channel-to-energy calibration helper, a fixed-angle Bragg
conversion helper, a deterministic calibration workflow, a versioned import
template for channel/count spectra and calibration standards, and a detector
response API for energy-domain stick peaks.

## Non-Goals

The detector response API is separated from crystallographic peak generation:
callers pass peak energies and integrated areas in counts. The startup response
helpers include an area-preserving Gaussian core, an optional one-sided
low-energy exponential tail hook, an optional fixed-energy escape peak hook,
and dead-time metadata recording. Detector-specific tail physics, pile-up,
nonlinearity, equation-of-state workflows, and high-pressure validation remain
future work.

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

## Related Files

- [sections/07_energy_dispersive_diffraction.md](sections/07_energy_dispersive_diffraction.md)
- [validation_baseline.md](validation_baseline.md)
