# Codex Prompt: Visualization Workstream

## Objective

Plan and implement a coherent sequence of issues in the **Visualization** workstream.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issues in this workstream

- #223: Implement profile plot data model (P1, phase: UX)
- #224: Implement multi-bank plot aggregation (P1, phase: UX)
- #225: Implement residual heatmap renderer (P1, phase: UX)
- #226: Implement parameter evolution chart data (P1, phase: UX)
- #227: Implement phase fraction evolution chart data (P1, phase: UX)
- #228: Implement covariance matrix renderer (P1, phase: UX)
- #229: Implement dependency graph renderer (P1, phase: UX)
- #230: Implement reflection browser (P1, phase: UX)
- #231: Implement mask and exclusion editor (P1, phase: UX)
- #232: Implement publication figure export (P1, phase: UX)

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
