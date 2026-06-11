# X-ray And Neutron Physics Helpers

This document covers the first lightweight Batch B physics helpers. They are
small validation and lookup utilities, not complete structure-factor engines.

## X-ray Wavelength Helpers

Location: `src/rietveld_next/xray/wavelength.py`

Functions:

```python
validate_wavelength_angstrom(wavelength_angstrom)
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

## Neutron Scattering-Length Lookup

Location: `src/rietveld_next/neutron/scattering_lengths.py`

Function:

```python
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

## Validation Limits

Tests cover known values and invalid-input handling. They do not yet provide a
complete cross-software diffraction validation example.
