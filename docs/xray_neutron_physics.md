# X-ray And Neutron Physics Helpers

This document covers the first lightweight Batch B physics helpers. They are
small validation and lookup utilities, not complete structure-factor engines.

## X-ray Wavelength Helpers

Location: `src/rietveld_next/xray/wavelength.py`

Functions:

```python
WavelengthMetadata(wavelength_angstrom, label=None, uncertainty_angstrom=None, provenance=None)
validate_wavelength_angstrom(wavelength_angstrom)
validate_wavelength_metadata(metadata)
bragg_two_theta_degrees(d_spacing_angstrom, wavelength_angstrom, *, order=1)
```

Units:

- `wavelength_angstrom` is the incident radiation wavelength in angstroms.
- `d_spacing_angstrom` is the lattice-plane spacing in angstroms.
- `bragg_two_theta_degrees` returns degrees two-theta.

Formula:

```text
n lambda = 2 d sin(theta)
two_theta = 2 theta
```

Validation:

- Wavelength and d-spacing values must be finite and positive.
- Diffraction order must be a positive integer.
- Unreachable Bragg conditions raise `ValueError` instead of returning a
  nonphysical angle.

## X-ray Instrument Metadata

Location: `src/rietveld_next/xray/instrument.py`

Records:

```python
LabCwXrdInstrument(...)
SynchrotronCwXrdInstrument(...)
```

The lab and synchrotron records are metadata models for continuous-wave X-ray
instrument setup. They validate wavelength metadata in angstroms and keep
synchrotron beamline fields separate from lab-source fields. These records do
not implement a fundamental-parameters instrument profile.

## X-ray Zero-Shift Calibration And Beamline Templates

Locations:

- `src/rietveld_next/xray/calibration.py`
- `src/rietveld_next/xray/beamline.py`

Records and functions:

```python
ZeroShiftCalibrationPoint(...)
calibrate_zero_shift(points, wavelength_angstrom=...)
SynchrotronBeamlineTemplate(...)
default_synchrotron_beamline_template(...)
```

The zero-shift workflow estimates a constant observed-minus-calculated
two-theta offset from reference d-spacings using Bragg's law. It reports the
weighted shift, weighted RMS residual, point count, wavelength, residuals, and
units. This is a deterministic calibration fixture, not a complete
least-squares instrument refinement.

The synchrotron beamline template records facility, beamline, detector, optional
monochromator/default wavelength metadata, and required beamline log fields. It
returns actionable missing-field diagnostics for import/preflight checks.

## X-ray Fundamental-Parameters Skeletons

Location: `src/rietveld_next/xray/fundamental_parameters.py`

Records and functions:

```python
EmissionLine(label, wavelength_angstrom, relative_intensity=1.0)
EmissionSpectrum(lines, reference_label=None)
ConstantAxialDivergence(fwhm_degrees)
ConstantDetectorResolution(fwhm_degrees)
TwoDimensionalIntegrationMetadata(...)
FundamentalParametersProfileModel(...)
evaluate_axial_divergence_fwhm(hook, two_theta_degrees)
evaluate_detector_resolution_fwhm(hook, two_theta_degrees)
xray_fundamental_parameters_capabilities()
```

The fundamental-parameters API is currently a documented composition skeleton.
It records emission-spectrum wavelengths in angstroms, hook FWHM contributions
in degrees two-theta, and 2D integration provenance links from source image URI
to integrated 1D profile URI. The profile evaluator delegates to the existing
Gaussian profile kernel and combines base, axial-divergence, and
detector-resolution FWHM terms in quadrature.

Validation:

- Emission-line wavelengths must be positive finite angstrom values.
- Relative line intensities must be finite and non-negative, with positive
  total spectrum intensity.
- Hook outputs must be finite non-negative FWHM values in degrees two-theta.
- Two-theta hook evaluation is restricted to `0 < two_theta < 180` degrees.
- 2D integration azimuth ranges must be ordered, bounded by `[-360, 360]`
  degrees, and span no more than 360 degrees.

Limitations:

- These APIs do not implement a validated Cheary-Coelho
  fundamental-parameters convolution.
- The constant axial-divergence and detector-resolution hooks are deterministic
  plumbing fixtures, not calibrated instrument-response models.
- The 2D integration metadata link records provenance only; it does not perform
  image integration.
- Capability declarations are exposed through
  `xray_fundamental_parameters_capabilities()` using the shared
  `PluginCapability` metadata model.

## X-ray Form Factors And Corrections

Locations:

- `src/rietveld_next/diffraction/scattering.py`
- `src/rietveld_next/diffraction/corrections.py`

Functions:

```python
available_xray_form_factor_symbols()
lookup_xray_form_factor_coefficients(symbol)
evaluate_xray_form_factor(symbol, sin_theta_over_wavelength_inv_angstrom)
simple_miller_multiplicity(hkl)
equivalent_miller_indices_by_sign_permutation(hkl)
lorentz_polarization_correction(two_theta_degrees, polarization_fraction=0.5)
```

The form-factor table is a deliberately tiny neutral-atom Cromer-Mann subset
for API plumbing and tests only. It currently covers `C`, `O`, and `Si`, with
provenance metadata on returned coefficient records. The multiplicity helper
counts sign/permutation equivalents and is not a space-group multiplicity
engine. The Lorentz-polarization helper implements a validated CW powder
reference expression for finite `0 < two_theta < 180` degree angles.

## Neutron Scattering-Length Lookup

Location: `src/rietveld_next/neutron/scattering_lengths.py`

Function:

```python
available_bound_coherent_scattering_lengths()
lookup_bound_coherent_scattering_length(isotope)
```

The lookup currently includes a deliberately small subset needed to establish
the API and tests:

| Key | Isotope label | Bound coherent length (fm) |
| --- | --- | ---: |
| `H` | `H` | -3.7390 |
| `nat H` | `H` | -3.7390 |
| `1H` | `1H` | -3.7406 |
| `2H` | `2H` | 6.671 |
| `D` | `2H` | 6.671 |
| `nat C` | `nat C` | 6.6460 |
| `nat O` | `nat O` | 5.803 |

The returned records include the provenance label `NIST Center for Neutron
Research bound coherent scattering length tables`. This implementation is not
yet a complete isotope table and should fail clearly for unsupported keys.

## Neutron Instrument And Correction Hooks

Locations:

- `src/rietveld_next/neutron/instrument.py`
- `src/rietveld_next/neutron/absorption.py`
- `src/rietveld_next/neutron/corrections.py`

Records and functions:

```python
NeutronScatterer(isotope, occupancy=1.0, multiplicity=1)
ContinuousWaveNeutronInstrument(...)
ConstantNeutronAbsorption(transmission)
LinearWavelengthNeutronAbsorption(...)
ConstantSampleGeometryCorrection(...)
SimplePrimaryExtinctionCorrection(...)
evaluate_sample_geometry_correction(...)
evaluate_extinction_correction(...)
```

The CW neutron instrument model records wavelength metadata and scatterers that
resolve through the neutron scattering-length table, not X-ray form factors.
The absorption API is a small hook/skeleton for wavelength-dependent
coefficients. It is intentionally not a validated full sample-geometry
absorption correction.

Sample-geometry and extinction APIs are optional correction hooks attached to
the CW neutron instrument. They multiply synthetic intensities independently of
the nuclear-amplitude helper and profile kernels. The constant geometry hook and
simple primary-extinction formula are deterministic validation fixtures only;
validated sample-shape, path-length, secondary-extinction, and instrument-
specific correction physics remain future work.

## Neutron Data Integration And Joint Weighting

Locations:

- `src/rietveld_next/neutron/background.py`
- `src/rietveld_next/neutron/mantid.py`
- `src/rietveld_next/neutron/weighting.py`
- `src/rietveld_next/neutron/uncertainty.py`
- `src/rietveld_next/neutron/validation_examples.py`

Records and functions:

```python
ContainerBackgroundModel(...)
import_mantid_reduced_data({"X": [...], "Y": [...], "E": [...]})
MantidReducedDataset(...)
NeutronDatasetWeighting(...)
JointNeutronWeightingModel(...)
check_neutron_uncertainties(...)
run_nuclear_neutron_validation_example()
```

`ContainerBackgroundModel` stores a non-negative additive container
background table and evaluates it by linear interpolation. Axis values are
strictly increasing and the default axis unit is `degrees_two_theta`; intensity
values and the default uncertainty unit are `counts`.

The Mantid adapter is dependency-free and accepts one documented reduced
workspace shape: `X` is either length `N` point centers or length `N + 1` bin
edges, while `Y` and optional `E` are length `N`. Bin-edge `X` arrays are
converted to centers before storage. The adapter records the shape assumption
in `MantidReducedDataset.to_dict()["metadata"]`.

Joint weighting uses `observed - calculated` residuals. The current supported
likelihood is `independent_gaussian`; weighting is either `inverse_variance`
with positive standard uncertainties or `unit` weighting for synthetic
monitor-normalized fixtures. `NeutronDatasetWeighting.to_dict()` records the
likelihood, weighting scheme, variance scale, relative dataset weight, and
auditable assumption notes.

Uncertainty checks return structured `ok`, `warning`, or `error` results.
Mismatched lengths and non-positive standard uncertainties are errors; values
below a configured relative floor are warnings so callers can decide whether to
raise, down-weight, or request user review.

Run the nuclear neutron validation example from a checkout with:

```bash
PYTHONPATH=src python3 -m rietveld_next.neutron.validation_examples
```

The example verifies a synthetic D2O-like bound coherent scattering-length sum
`2 * b(2H) + b(nat O) = 19.145 fm` using the package lookup table. It is a
deterministic API validation example, not a cross-software structure-factor
validation benchmark. The same limitation is recorded in
[ground_truths.md](ground_truths.md).

## Validation Limits

Tests cover known values and invalid-input handling. They do not yet provide a
complete cross-software diffraction validation example.
