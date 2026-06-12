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

`compare_gaussian_profile_outputs()` and
`run_rust_jax_gaussian_comparison()` provide the issue #294 comparison boundary.
When a Rust profile vector is supplied and JAX is available, the comparison
reports sample count, maximum absolute error, maximum relative error, checksum
absolute error, and the applied tolerance policy. Float64 uses strict
`1e-12` absolute and relative tolerances; float32 uses explicitly relaxed
`5e-5` absolute and relative tolerances. Without a Rust vector or JAX runtime,
the hook returns a structured skipped result rather than fabricating a
cross-backend result.

## Pseudo-Voigt And Profile Windowing Benchmarks

Functions:

```python
run_pseudo_voigt_profile_benchmark(size="small")
run_profile_windowing_benchmark(size="small")
```

Behavior:

- `run_pseudo_voigt_profile_benchmark()` evaluates the dependency-free
  area-scaled pseudo-Voigt reference kernel over deterministic synthetic peak
  datasets. It supports the shared `small`, `medium`, and opt-in `large`
  presets, reports checksum and runtime statistics, and records the evaluated
  point-peak pair count.
- The pseudo-Voigt benchmark differs from the Gaussian proxy because it mixes
  Lorentzian and Gaussian terms with an explicit `eta` parameter. The synthetic
  dataset remains a benchmark workload generator, not a scientific validation
  corpus.
- `run_profile_windowing_benchmark()` compares finite-window Gaussian profile
  evaluation against a dense all-peak/all-point Gaussian reference. It reports
  dense and windowed point-peak pairs, pair-count reduction, float64 pair-memory
  estimates, checksum, runtime statistics, maximum absolute error, maximum
  relative error, and the explicit truncation tolerance.
- The windowing smoke benchmark uses a Gaussian profile by default because
  pseudo-Voigt Lorentzian tails are nonzero outside any finite window. Future
  pseudo-Voigt windowing measurements should report tail-truncation tolerances
  explicitly rather than claiming exact equality.

The CLI runner selects these numerical kernels with `--kernel`:

```bash
PYTHONPATH=src python3 -m rietveld_next.benchmarks.runner --kernel pseudo_voigt_profile --size small
PYTHONPATH=src python3 -m rietveld_next.benchmarks.runner --kernel profile_windowing --size small
PYTHONPATH=src python3 -m rietveld_next.benchmarks.runner --kernel rust_jax_gaussian_comparison --size small
```

## Local Optimizer Benchmark

Function:

```python
run_local_optimizer_benchmark(dimensions=2)
```

Behavior:

- Runs a deterministic bounded quadratic objective.
- Reports runtime, optimizer iterations, function evaluations, final objective,
  convergence status, parameter-error metrics, an unbounded LM-compatible
  quadratic case, and a structured invalid-initial-model failure case.
- Uses the shared `BenchmarkResult` record.
- Remains opt-in; it is covered by a small smoke test but is not an expensive
  benchmark workload.

## Optimizer Follow-Up Benchmarks

Additional Batch C smoke hooks are available in
`src/rietveld_next/benchmarks/optimizer.py`:

```python
run_sparse_jacobian_assembly_benchmark(dimensions=4)
run_automatic_differentiation_benchmark(dimensions=2)
run_optimizer_scaling_benchmark(max_dimensions=4)
run_global_multistart_benchmark(dimensions=2, start_count=3)
```

The automatic-differentiation benchmark uses optional JAX `jacfwd` when JAX is
available with float64 enabled. If JAX is unavailable, it returns a structured
skipped result rather than falling back silently to finite differences.

## Workflow, AI, HPC, And Physics Proxy Benchmarks

Additional opt-in smoke hooks live in:

- `src/rietveld_next/benchmarks/workflow_ai_hpc.py`
- `src/rietveld_next/benchmarks/physics_proxies.py`
- `src/rietveld_next/benchmarks/storage_visualization_diagnostics.py`

Public API:

```python
run_sequential_refinement_workflow_overhead_benchmark()
run_ai_tool_call_overhead_benchmark()
run_slurm_job_array_packaging_benchmark(output_directory=...)
run_multi_bank_tof_profile_proxy_benchmark()
run_neutron_scattering_lookup_proxy_benchmark()
run_magnetic_structure_factor_proxy_benchmark()
run_edxrd_detector_response_proxy_benchmark()
run_project_package_storage_benchmark(output_dir=...)
run_visualization_decimation_benchmark()
run_residual_diagnostics_benchmark()
```

These functions are small synthetic benchmarks for issue-scoped plumbing. They
record sizes, timings, checksums, units, assumptions, and relevant issue
numbers in the shared `BenchmarkResult` schema. They do not submit real cluster
jobs, do not call an LLM, and do not claim cross-software scientific
validation. Larger workflow, AI, HPC, or physics benchmarks remain opt-in
follow-up work.

The benchmark runner integrates the sequential workflow smoke benchmark through
`--family workflow --backend python`; other non-numerical families remain
structured skipped selections until their runner paths are assigned.
