# TOF Refinement Guide

## Purpose

This guide describes the current TOF metadata and calibration foundation for
contributors and agents.

## Scope

The current implementation provides TOF histogram axes, detector-bank metadata,
and calibration parameter containers. It supports typed records and validation,
not full TOF profile refinement.

## Non-Goals

Back-to-back exponential profile kernels, multi-bank objective assembly, and
facility-grade GSAS-II TOF comparison fixtures remain future work.

## Example

Use `src/rietveld_next/tof/` helpers to define positive, increasing TOF bin
edges in microseconds and bank-specific calibration metadata before connecting
them to project histograms.

## Related Files

- [sections/06_tof_and_neutron_requirements.md](sections/06_tof_and_neutron_requirements.md)
- [validation_baseline.md](validation_baseline.md)
