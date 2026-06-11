# Codex Prompt: Issue #304 — Benchmark global multi-start refinement workflow

## Objective

Complete GitHub issue `#304`: **Benchmark global multi-start refinement workflow**.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issue metadata

- Category: `Benchmarking`
- Phase: `Optimization Benchmarks`
- Priority: `P2`
- Labels: `benchmarking, codex-ready, global-optimization, performance, workflow`

## Dependencies

- #302

## Scope

Benchmark multi-start or differential-evolution assisted refinement workflows on synthetic multimodal problems.

## Description

Implement or specify `Benchmark global multi-start refinement workflow` as part of the Rietveld Next benchmarking workstream. Keep the change small, reviewable, deterministic, and aligned with the `src/`-first repository layout.

## Required deliverables

- Global optimization benchmark
- Multi-start result archive
- Summary statistics

## Acceptance criteria

- Benchmark stores all candidate results, not only the winner.
- Output reports best objective, success rate, total evaluations, and wall time.
- Random seeds are fixed and recorded.
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
