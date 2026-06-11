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

## Neutron Instrument And Absorption Hooks

Locations:

- `src/rietveld_next/neutron/instrument.py`
- `src/rietveld_next/neutron/absorption.py`

Records and functions:

```python
NeutronScatterer(isotope, occupancy=1.0, multiplicity=1)
ContinuousWaveNeutronInstrument(...)
ConstantNeutronAbsorption(transmission)
LinearWavelengthNeutronAbsorption(...)
```

The CW neutron instrument model records wavelength metadata and scatterers that
resolve through the neutron scattering-length table, not X-ray form factors.
The absorption API is a small hook/skeleton for wavelength-dependent
coefficients. It is intentionally not a validated full sample-geometry
absorption correction.

## Validation Limits

Tests cover known values and invalid-input handling. They do not yet provide a
complete cross-software diffraction validation example.
