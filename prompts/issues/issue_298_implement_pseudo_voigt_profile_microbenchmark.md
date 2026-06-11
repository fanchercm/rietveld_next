# Codex Prompt: Issue #298 — Implement pseudo-Voigt profile microbenchmark

## Objective

Complete GitHub issue `#298`: **Implement pseudo-Voigt profile microbenchmark**.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issue metadata

- Category: `Benchmarking`
- Phase: `Numerical Benchmarks`
- Priority: `P1`
- Labels: `benchmarking, codex-ready, diffraction, performance`

## Dependencies

- #292
- #293

## Scope

Add a pseudo-Voigt profile benchmark to better approximate common Rietveld profile workloads beyond Gaussian peaks.

## Description

Implement or specify `Implement pseudo-Voigt profile microbenchmark` as part of the Rietveld Next benchmarking workstream. Keep the change small, reviewable, deterministic, and aligned with the `src/`-first repository layout.

## Required deliverables

- Pseudo-Voigt kernel benchmark
- Synthetic data preset
- Rust and/or JAX implementation depending on available backend

## Acceptance criteria

- Benchmark supports at least small and medium sizes.
- Output includes checksum and runtime statistics.
- Documentation explains differences from the Gaussian proxy benchmark.
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
