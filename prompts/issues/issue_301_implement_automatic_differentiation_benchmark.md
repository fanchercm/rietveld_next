# Codex Prompt: Issue #301 — Implement automatic differentiation benchmark

## Objective

Complete GitHub issue `#301`: **Implement automatic differentiation benchmark**.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issue metadata

- Category: `Benchmarking`
- Phase: `Numerical Benchmarks`
- Priority: `P1`
- Labels: `ad, benchmarking, codex-ready, jax, performance`

## Dependencies

- #300

## Scope

Benchmark JAX automatic differentiation for profile residuals and compare against finite-difference or analytic derivative references where available.

## Description

Implement or specify `Implement automatic differentiation benchmark` as part of the Rietveld Next benchmarking workstream. Keep the change small, reviewable, deterministic, and aligned with the `src/`-first repository layout.

## Required deliverables

- AD benchmark
- Derivative correctness check
- Compile/steady-state timing output

## Acceptance criteria

- AD benchmark separates compilation from execution.
- Derivative shape and checksum are reported.
- Small-case derivative agrees with reference within tolerance.
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
