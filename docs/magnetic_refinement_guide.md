# Magnetic Refinement Guide

## Purpose

This guide records the current magnetic refinement metadata model.

## Scope

The current foundation includes magnetic moment records, propagation vectors,
magnetic form-factor lookup helpers, mCIF scalar import reports, magnetic
symmetry constraint records, representation-analysis import placeholders, and
project-level magnetic-structure metadata. M25 adds deterministic
nuclear-plus-magnetic startup coupling, magnetic reflection flagging, a
synthetic tutorial dataset, report-section generation, and staged magnetic
parameter recipes. Vectors carry explicit component shape validation, import
helpers report unsupported fields, and form-factor records carry provenance.

## Non-Goals

Complete loop-aware mCIF import, numerical representation-analysis basis-vector
interpretation, complete magnetic form-factor coverage, and validated magnetic
structure factors are not complete. The M25 tutorial dataset uses relative
synthetic intensities and does not validate material-specific magnetic
structure-factor physics.

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

## mCIF Import Skeleton

Location: `src/rietveld_next/neutron/magnetic/imports.py`

Function:

```python
parse_magnetic_cif_skeleton(text)
```

The M24 mCIF importer is a deterministic scalar-field skeleton. It accepts one
`data_` block name and a small set of scalar cell and magnetic-space-group
fields, including `_cell_length_a`, `_cell_angle_alpha`, and
`_magnetic_space_group_name_BNS`. Unsupported tags and `loop_` constructs are
reported in `unsupported_fields`; they are not silently dropped. Duplicate
supported scalar fields and malformed scalar lines raise `ValueError`. Cell
length fields are validated as positive Angstrom values, and cell angle fields
are validated as degrees greater than 0 and less than 180.

The result schema is labeled `m24-mcif-skeleton-v1`. It is intended for import
plumbing and diagnostics, not for complete magnetic structure reconstruction.

## Magnetic Symmetry Constraints

Location: `src/rietveld_next/neutron/magnetic/symmetry.py`

Functions:

```python
magnetic_moment_parameter_path(phase_id, site_id, component)
magnetic_moment_parameter_id(phase_id, site_id, component)
create_collinear_moment_constraint(...)
```

Magnetic moment parameter paths use the core parameter-graph convention:

```text
phase/<phase_id>/magnetic_structure/sites/<site_id>/moment/<mx|my|mz>
```

`MagneticSymmetryConstraint` records symbolic moment constraints in Bohr
magnetons and converts to the shared core `Constraint` model with
`kind="symbolic"`. The startup helper covers deterministic collinear component
relations of the form:

```text
constrained_component = multiplier * reference_component
```

Invalid components, non-finite multipliers, empty parameter IDs, and unsupported
units raise `ValueError`.

## Joint Nuclear-Magnetic Startup Helpers

Location: `src/rietveld_next/neutron/magnetic/joint.py`

Functions:

```python
NuclearMagneticPhaseCoupling(...)
flag_magnetic_reflections(reflections, propagation_vectors)
create_magnetic_refinement_tutorial_dataset()
generate_magnetic_report_section(dataset)
build_magnetic_parameter_group_recipes(phase_id, site_ids)
```

`NuclearMagneticPhaseCoupling` stores contribution toggles and non-negative
relative scales for one phase. It accepts nuclear and magnetic relative
intensity vectors of equal length and returns separated or summed
contributions. Invalid units, non-finite scales, negative intensities, and
mismatched vector lengths raise `ValueError`.

Reflection flagging classifies reciprocal-lattice-unit coordinates as
`nuclear`, `magnetic_satellite`, `mixed_nuclear_magnetic`, or `unindexed`.
Integer Miller indices are treated as nuclear. Offsets that match `+k` or `-k`
within the explicit `tolerance_rlu` are treated as magnetic satellites. A zero
propagation vector at integer `hkl` is reported as mixed. This is a deterministic
indexing helper, not a magnetic extinction-rule engine.

The tutorial fixture is returned by:

```python
dataset = create_magnetic_refinement_tutorial_dataset()
dataset.calculated_intensity
```

The fixture uses a collinear Mn-like synthetic phase, propagation vector
`(0.5, 0.0, 0.0)` in reciprocal lattice units, relative nuclear and magnetic
intensity arrays, and explicit notes that the values are not cross-software
validation data.

The report generator returns a Markdown section with separated nuclear,
magnetic, and total relative intensity sums, reflection-flag counts, staged
parameter recipes, and limitations. It is deterministic and suitable for
workflow reports that need to disclose what was toggled or held fixed.

`build_magnetic_parameter_group_recipes` emits three startup stages:

1. Refine magnetic scale with the nuclear baseline fixed.
2. Refine longitudinal `mz` moment components.
3. Release transverse `mx` and `my` components after scale and primary axis
   are stable.

Moment-component parameter IDs use the same canonical magnetic-structure paths
as the symmetry helpers. Recipe bounds are finite and explicit: the default
component bound is `[-10, 10]` Bohr magnetons and the startup magnetic-scale
guard bound is `[0, 1e6]` in relative intensity units.

## Representation-Analysis Placeholder

Location: `src/rietveld_next/neutron/magnetic/imports.py`

Function:

```python
create_representation_analysis_placeholder(payload)
```

The representation-analysis API currently records source-tool provenance,
declared irrep labels, declared basis-vector count, and a documented extension
contract. It returns `status="placeholder"` and does not interpret basis-vector
matrices. A complete importer must provide at least source-tool metadata,
parent space group, propagation vector in reciprocal lattice units, irrep
labels, basis vectors, site mapping, normalization convention, and provenance.

## Example

Record propagation vectors as three-component vectors and magnetic moments with
units and coordinate frames. Use magnetic form-factor lookups only for supported
startup ions, keep mCIF import reports explicit about unsupported fields, use
joint-refinement helpers to keep nuclear and magnetic contributions reported
separately, and keep validation reports explicit about whether magnetic
quantities are metadata-only, rounded table evaluations, synthetic tutorial
fixtures, placeholders, or compared against reference software.

## Related Files

- [sections/06_tof_and_neutron_requirements.md](sections/06_tof_and_neutron_requirements.md)
- [core_data_model.md](core_data_model.md)
