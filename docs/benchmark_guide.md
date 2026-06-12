# Benchmark Guide

## Purpose

This guide defines benchmark expectations for contributors.

## Scope

Benchmarks are opt-in smoke or measurement hooks under
`src/rietveld_next/benchmarks/`. Benchmark outputs should use
`BenchmarkResult` records and distinguish compile/setup, warmup, and
steady-state timing.

## Non-Goals

Benchmarks are not scientific validation reports. They must not run expensive
GPU, cluster, or facility workloads in default unit tests.

## Example

Return a structured skipped result when an optional backend such as JAX is not
available, and include environment metadata for reproducibility.

Numerical profile examples can be selected through the runner:

```bash
PYTHONPATH=src python3 -m rietveld_next.benchmarks.runner --kernel pseudo_voigt_profile --size small
PYTHONPATH=src python3 -m rietveld_next.benchmarks.runner --kernel profile_windowing --size small
```

## Related Files

- [backend_benchmarks.md](backend_benchmarks.md)
- [validation_baseline.md](validation_baseline.md)
