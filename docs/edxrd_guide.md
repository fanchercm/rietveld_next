# EDXRD Guide

## Purpose

This guide describes the current energy-dispersive X-ray diffraction foundation.

## Scope

The current EDXRD package stores positive energy axes in keV and provides a
linear or polynomial channel-to-energy calibration helper, a fixed-angle Bragg
conversion helper, a deterministic calibration workflow, and a versioned import
template for channel/count spectra and calibration standards.

## Non-Goals

Detector response kernels, escape-peak correction, dead-time correction,
equation-of-state workflows, and high-pressure validation are future work.

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

## Related Files

- [sections/07_energy_dispersive_diffraction.md](sections/07_energy_dispersive_diffraction.md)
- [validation_baseline.md](validation_baseline.md)
