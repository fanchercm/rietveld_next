# Magnetic Refinement Guide

## Purpose

This guide records the current magnetic refinement metadata model.

## Scope

The current foundation includes magnetic moment records, propagation vectors,
magnetic form-factor lookup helpers, and project-level magnetic-structure
metadata. Vectors carry explicit component shape validation, and form-factor
records carry provenance.

## Non-Goals

Magnetic symmetry constraints, representation analysis import, complete magnetic
form-factor coverage, and validated magnetic structure factors are not complete.

## Magnetic Form Factors

Location: `src/rietveld_next/neutron/magnetic/form_factors.py`

Functions:

```python
available_magnetic_form_factor_ions()
lookup_magnetic_form_factor_coefficients(ion)
evaluate_magnetic_form_factor(ion, scattering_vector_inv_angstrom)
normalize_magnetic_ion_label(ion)
```

The magnetic form-factor table is a deliberately tiny `<j0>` startup subset for
`Mn2+`, `Fe2+`, and `Ni2+`. It uses the Brown International Tables coefficient
form:

```text
<j0(Q)> = sum_i a_i exp(-b_i * (Q / 4*pi)^2) + c
```

`Q` is the scattering-vector magnitude in inverse angstroms, and returned form
factors are dimensionless. Lookup records include source and scope-note
provenance. Unsupported ions raise clear `KeyError` exceptions; invalid labels
or non-finite/negative `Q` values raise `ValueError`.

## Example

Record propagation vectors as three-component vectors and magnetic moments with
units and coordinate frames. Use magnetic form-factor lookups only for supported
startup ions, and keep validation reports explicit about whether magnetic
quantities are metadata-only, rounded table evaluations, or compared against
reference software.

## Related Files

- [sections/06_tof_and_neutron_requirements.md](sections/06_tof_and_neutron_requirements.md)
- [core_data_model.md](core_data_model.md)
