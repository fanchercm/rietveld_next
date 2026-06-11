# ADR 0002: Use a Hybrid Project Package

## Status

Proposed

## Decision

Use JSON Schema for semantic model, NeXus/HDF5 for facility data, Zarr for cloud-scale arrays, Parquet/Arrow for result tables, and JSONL for provenance.

## Consequences

No single file format is forced to solve every problem. Packaging and reference management must be robust.
