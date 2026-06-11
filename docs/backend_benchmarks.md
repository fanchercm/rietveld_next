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
