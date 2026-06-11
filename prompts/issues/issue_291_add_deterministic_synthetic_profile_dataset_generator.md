# Codex Prompt: Issue #291 — Add deterministic synthetic profile dataset generator

## Objective

Complete GitHub issue `#291`: **Add deterministic synthetic profile dataset generator**.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issue metadata

- Category: `Benchmarking`
- Phase: `Benchmark Foundation`
- Priority: `P0`
- Labels: `benchmarking, codex-ready, data, performance`

## Dependencies

- #290

## Scope

Implement deterministic synthetic data generation for profile-evaluation benchmarks, including x arrays, peak positions, amplitudes, widths, and metadata.

## Description

Implement or specify `Add deterministic synthetic profile dataset generator` as part of the Rietveld Next benchmarking workstream. Keep the change small, reviewable, deterministic, and aligned with the `src/`-first repository layout.

## Required deliverables

- Synthetic dataset generator
- Small/medium/large presets
- Determinism tests

## Acceptance criteria

- Repeated generation with the same seed produces identical arrays and metadata.
- Presets include small, medium, and large sizes.
- Generator records all parameters needed to reproduce the dataset.
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
