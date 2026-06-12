# Neutron Refinement Guide

## Purpose

This guide documents the current neutron foundation and its limitations.

## Scope

The repository currently includes CW neutron instrument metadata,
provenance-labeled scattering-length lookup rows, and wavelength-dependent
absorption hook skeletons.

## Non-Goals

The current helpers are not a complete neutron refinement engine. Sample
geometry corrections, extinction, Mantid import, and joint weighting remain
separate open work.

## Example

Use neutron instrument records to preserve wavelength and radiation metadata,
then document any correction assumptions in validation reports before comparing
results across datasets.

## Related Files

- [xray_neutron_physics.md](xray_neutron_physics.md)
- [sections/06_tof_and_neutron_requirements.md](sections/06_tof_and_neutron_requirements.md)
