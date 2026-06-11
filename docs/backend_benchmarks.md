# Backend Benchmark Hooks

Benchmark helpers live under `src/rietveld_next/benchmarks/` so the repository
does not need a forbidden top-level `benchmarks/` directory.

## Result Records

`BenchmarkResult` and `BenchmarkTiming` provide a deterministic
JSON-compatible shape for Python, JAX, and Rust-style benchmark outputs.
Completed results include:

- benchmark name and backend
- dtype and input size
- measured iterations and warmup count
- checksum
- median, minimum, maximum runtime
- optional compile/setup time
- environment metadata

Skipped results use `status="skipped"` and must include `skip_reason`.

`benchmark_result_schema()` returns a dependency-free JSON-schema-like mapping
for the shared result shape, and `validate_benchmark_result_dict()` validates
serialized benchmark records without requiring an external schema package.

## Taxonomy And Synthetic Datasets

Locations:

- `src/rietveld_next/benchmarks/taxonomy.py`
- `src/rietveld_next/benchmarks/datasets.py`

Benchmark identifiers use this stable shape:

```text
workstream.kernel.backend.size.variant
```

The initial taxonomy distinguishes microbenchmarks, integration benchmarks,
scientific-validation benchmarks, and workflow benchmarks. Synthetic Gaussian
profile datasets are deterministic and record size, seed, axis units, and peak
metadata. Large presets are opt-in and are not part of the default test suite.

## Runner Skeleton

Location: `src/rietveld_next/benchmarks/runner.py`

The runner parses benchmark family, backend, size, iterations, warmup, dtype,
seed, and optional output paths. Unsupported or unavailable backends return
structured skipped results instead of failing the command. JSON output and a
small Markdown summary can be generated from the same result record.

## JAX Gaussian Microbenchmark

Function:

```python
run_jax_gaussian_microbenchmark(
    input_size=256,
    iterations=5,
    warmup=1,
    dtype="float64",
)
```

Behavior:

- Imports JAX only inside the runner.
- Returns a skipped benchmark result when JAX is unavailable.
- Uses `jax.jit` and reports first-call compile time separately from
  steady-state timing.
- Returns a skipped result for `dtype="float64"` when `jax_enable_x64` is not
  enabled, so requested precision is not silently downgraded.
- Calls `.block_until_ready()` before stopping timers.
- Reports dtype and device metadata when the benchmark runs.

This hook is opt-in and is not part of the default unit-test workload.

## Rust Backend Status

The shared result record can represent Rust benchmark output, and tests include
a Rust-style result fixture. A compiled Rust numerical package and executable
are not yet present in this repository snapshot, so a real Rust Gaussian
microbenchmark remains follow-up work.

## Local Optimizer Benchmark

Function:

```python
run_local_optimizer_benchmark(dimensions=2)
```

Behavior:

- Runs a deterministic bounded quadratic objective.
- Reports runtime, optimizer iterations, function evaluations, final objective,
  convergence status, and parameter-error metrics.
- Uses the shared `BenchmarkResult` record.
- Remains opt-in; it is covered by a small smoke test but is not an expensive
  benchmark workload.
