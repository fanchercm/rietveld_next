# EDXRD Guide

## Purpose

This guide describes the current energy-dispersive X-ray diffraction foundation.

## Scope

The current EDXRD package stores positive energy axes in keV and provides a
linear channel-to-energy calibration helper plus fixed-angle Bragg conversion
metadata.

## Non-Goals

Detector response kernels, escape-peak correction, dead-time correction,
equation-of-state workflows, and high-pressure validation are future work.

## Example

Use EDXRD axis helpers to preserve channel/energy units, then record
calibration coefficients and fixed angle assumptions in project metadata and
validation reports.

## Related Files

- [sections/07_energy_dispersive_diffraction.md](sections/07_energy_dispersive_diffraction.md)
- [validation_baseline.md](validation_baseline.md)
