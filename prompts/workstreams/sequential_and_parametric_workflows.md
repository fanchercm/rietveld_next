# Codex Prompt: Sequential and Parametric Workflows Workstream

## Objective

Plan and implement a coherent sequence of issues in the **Sequential and Parametric Workflows** workstream.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issues in this workstream

- #168: Implement sequential runner (P1, phase: Workflows)
- #169: Implement sequential result table (P1, phase: Workflows)
- #170: Implement previous-point initialization (P1, phase: Workflows)
- #171: Implement failed-point retry policy (P1, phase: Workflows)
- #172: Implement parameter evolution export (P1, phase: Workflows)
- #173: Implement parametric model expression API (P1, phase: Workflows)
- #174: Implement temperature-dependent parameter model (P1, phase: Workflows)
- #175: Implement pressure-dependent parameter model (P1, phase: Workflows)
- #176: Implement sequential dashboard data API (P1, phase: Workflows)
- #177: Implement residual heatmap data export (P1, phase: Workflows)
- #178: Implement batch recipe format (P1, phase: Workflows)
- #179: Implement workflow replay command (P1, phase: Workflows)
- #180: Implement workflow checkpointing (P1, phase: Workflows)
- #181: Implement workflow comparison report (P1, phase: Workflows)
- #182: Implement high-throughput result summary (P1, phase: Workflows)

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
