# Codex Prompt: Issue #317 — Benchmark visualization data decimation

## Objective

Complete GitHub issue `#317`: **Benchmark visualization data decimation**.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issue metadata

- Category: `Benchmarking`
- Phase: `Visualization Benchmarks`
- Priority: `P2`
- Labels: `benchmarking, codex-ready, performance, ux, visualization`

## Dependencies

- None

## Scope

Benchmark decimation or downsampling of large observed/calculated/difference arrays for interactive plotting.

## Description

Implement or specify `Benchmark visualization data decimation` as part of the Rietveld Next benchmarking workstream. Keep the change small, reviewable, deterministic, and aligned with the `src/`-first repository layout.

## Required deliverables

- Decimation benchmark
- Visual-data fixture
- Accuracy/performance report

## Acceptance criteria

- Benchmark reports input size, output size, runtime, and preserved extrema count or equivalent quality metric.
- Small deterministic test verifies extrema preservation if algorithm claims it.
- No browser automation is required for this issue.
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
