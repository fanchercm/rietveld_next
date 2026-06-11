# Codex Prompt: Benchmarking Workstream

## Objective

Plan and implement a coherent sequence of issues in the **Benchmarking** workstream.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issues in this workstream

- #288: Define benchmark taxonomy and naming convention (P0, phase: Benchmark Foundation)
- #289: Create benchmark result schema (P0, phase: Benchmark Foundation)
- #290: Create benchmark runner CLI skeleton (P0, phase: Benchmark Foundation)
- #291: Add deterministic synthetic profile dataset generator (P0, phase: Benchmark Foundation)
- #292: Implement Rust Gaussian profile microbenchmark (P0, phase: Numerical Benchmarks)
- #293: Implement JAX Gaussian profile microbenchmark (P0, phase: Numerical Benchmarks)
- #294: Compare Rust and JAX Gaussian profile outputs (P0, phase: Numerical Benchmarks)
- #295: Add Markdown benchmark report generation (P1, phase: Benchmark Foundation)
- #296: Add benchmark environment metadata capture (P1, phase: Benchmark Foundation)
- #297: Add benchmark skip policy for optional dependencies (P1, phase: Benchmark Foundation)
- #298: Implement pseudo-Voigt profile microbenchmark (P1, phase: Numerical Benchmarks)
- #299: Implement profile windowing benchmark (P1, phase: Numerical Benchmarks)
- #300: Implement sparse Jacobian assembly benchmark (P1, phase: Numerical Benchmarks)
- #301: Implement automatic differentiation benchmark (P1, phase: Numerical Benchmarks)
- #302: Implement local optimizer benchmark harness (P1, phase: Optimization Benchmarks)
- #303: Benchmark optimizer scaling with parameter count (P2, phase: Optimization Benchmarks)
- #304: Benchmark global multi-start refinement workflow (P2, phase: Optimization Benchmarks)
- #305: Implement sequential refinement benchmark (P1, phase: Workflow Benchmarks)
- #306: Implement parametric refinement benchmark (P2, phase: Workflow Benchmarks)
- #307: Implement batch throughput benchmark (P1, phase: Workflow Benchmarks)
- #308: Implement multi-bank TOF profile benchmark (P1, phase: TOF Benchmarks)
- #309: Benchmark TOF calibration refinement (P2, phase: TOF Benchmarks)
- #310: Implement neutron scattering factor table lookup benchmark (P2, phase: Neutron Benchmarks)
- #311: Implement magnetic structure-factor proxy benchmark (P2, phase: Magnetic Benchmarks)
- #312: Implement EDXRD detector-response benchmark (P1, phase: EDXRD Benchmarks)
- #313: Benchmark EDXRD calibration workflow (P2, phase: EDXRD Benchmarks)
- #314: Benchmark storage write/read for project packages (P1, phase: Storage Benchmarks)
- #315: Benchmark Zarr profile-array IO (P2, phase: Storage Benchmarks)
- #316: Benchmark Parquet result-table IO (P2, phase: Storage Benchmarks)
- #317: Benchmark visualization data decimation (P2, phase: Visualization Benchmarks)
- #318: Benchmark residual diagnostic computation (P1, phase: Diagnostics Benchmarks)
- #319: Benchmark covariance and correlation computation (P1, phase: Diagnostics Benchmarks)
- #320: Benchmark AI tool-call overhead (P2, phase: AI Benchmarks)
- #321: Benchmark agent replay and provenance validation (P2, phase: AI Benchmarks)
- #322: Benchmark Slurm job-array packaging overhead (P2, phase: HPC Benchmarks)
- #323: Benchmark Ray or Dask local scheduler overhead (P2, phase: HPC Benchmarks)
- #324: Add benchmark regression baseline mechanism (P1, phase: Benchmark Infrastructure)
- #325: Add benchmark dashboard artifact generation (P2, phase: Benchmark Infrastructure)
- #326: Add benchmark documentation hub (P1, phase: Benchmark Infrastructure)
- #327: Create benchmark validation CI workflow (P1, phase: Benchmark Infrastructure)

## Execution guidance

- Start with P0 issues and dependency-free issues.
- Prefer milestone prompts for multi-issue implementation.
- Prefer individual issue prompts for targeted pull requests.
- Keep scientific claims tied to tests, fixtures, or documentation.
- Avoid broad rewrites unless an issue explicitly requires an architecture change.

## Final response requested from Codex

Report:

- Issues completed.
- Issues partially completed.
- Tests and validation commands run.
- Follow-up issue recommendations.
