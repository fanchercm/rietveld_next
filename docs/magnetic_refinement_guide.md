# Magnetic Refinement Guide

## Purpose

This guide records the current magnetic refinement metadata model.

## Scope

The current foundation includes magnetic moment records, propagation vectors,
and project-level magnetic-structure metadata. Vectors carry explicit component
shape validation and provenance.

## Non-Goals

Magnetic symmetry constraints, representation analysis import, magnetic form
factor tables, and validated magnetic structure factors are not complete.

## Example

Record propagation vectors as three-component vectors and magnetic moments with
units and coordinate frames. Validation reports must state whether magnetic
quantities are metadata-only or compared against reference software.

## Related Files

- [sections/06_tof_and_neutron_requirements.md](sections/06_tof_and_neutron_requirements.md)
- [core_data_model.md](core_data_model.md)
