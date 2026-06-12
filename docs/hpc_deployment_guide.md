# HPC Deployment Guide

## Purpose

This guide describes the current HPC execution boundary and deployment
expectations.

## Scope

The current package includes scheduler abstractions, local/dry-run execution,
Slurm metadata helpers, retry policy records, object-store URI metadata, and
provenance capture.

## Non-Goals

Default tests do not submit real cluster jobs, contact cloud services, or write
distributed result databases.

## Example

Use local or dry-run schedulers for CI. Cluster adapters must record job
metadata, environment assumptions, retry behavior, and result provenance before
running facility workloads.

## Related Files

- [sections/10_hpc_and_cloud_strategy.md](sections/10_hpc_and_cloud_strategy.md)
- [validation_baseline.md](validation_baseline.md)
