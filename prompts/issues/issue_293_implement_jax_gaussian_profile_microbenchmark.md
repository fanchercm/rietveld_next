# Codex Prompt: Issue #293 — Implement JAX Gaussian profile microbenchmark

## Objective

Complete GitHub issue `#293`: **Implement JAX Gaussian profile microbenchmark**.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issue metadata

- Category: `Benchmarking`
- Phase: `Numerical Benchmarks`
- Priority: `P0`
- Labels: `benchmarking, codex-ready, jax, performance, python`

## Dependencies

- #291

## Scope

Implement the JAX Gaussian profile-sum benchmark with compile time separated from steady-state execution time.

## Description

Implement or specify `Implement JAX Gaussian profile microbenchmark` as part of the Rietveld Next benchmarking workstream. Keep the change small, reviewable, deterministic, and aligned with the `src/`-first repository layout.

## Required deliverables

- JAX Gaussian profile function
- JAX timing harness
- Benchmark JSON output

## Acceptance criteria

- JAX function is JIT compiled.
- First-call compile time is reported separately from steady-state runtime.
- The benchmark uses `.block_until_ready()` before stopping timers.
- All implementation source is placed under `src/`; no forbidden top-level implementation directories are created.
- Benchmark can be skipped or constrained in normal CI so expensive workloads do not run by default.
- Results are reproducible with fixed seeds, explicit dataset sizes, software versions, and hardware metadata where available.

## Implementation instructions

1. Keep the change small enough for a focused pull request.
2. Prefer extending existing files and APIs over creating parallel duplicate implementations.
3. Add or update tests where the issue changes behavior.
4. Add docs or examples when the issue introduces a public interface or workflow.
5. Do not run expensive benchmarks or validation cases in default CI unless the issue explicitly requires it.
6. Keep generated artifacts deterministic.
7. Verify no forbidden top-level implementation directories were created.

## Final response requested from Codex

Report:

- Files changed.
- Tests run.
- Acceptance criteria satisfied.
- Remaining work or follow-up issues.
