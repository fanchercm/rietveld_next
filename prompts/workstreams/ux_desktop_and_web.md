# Codex Prompt: UX Desktop and Web Workstream

## Objective

Plan and implement a coherent sequence of issues in the **UX Desktop and Web** workstream.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issues in this workstream

- #203: Implement desktop shell src layout (P1, phase: UX)
- #204: Implement project open screen (P1, phase: UX)
- #205: Implement data import screen (P1, phase: UX)
- #206: Implement CIF validation screen (P1, phase: UX)
- #207: Implement pattern viewer (P1, phase: UX)
- #208: Implement reflection tick overlay (P1, phase: UX)
- #209: Implement difference plot panel (P1, phase: UX)
- #210: Implement parameter table (P1, phase: UX)
- #211: Implement parameter graph view (P1, phase: UX)
- #212: Implement constraint editor (P1, phase: UX)
- #213: Implement correlation heatmap (P1, phase: UX)
- #214: Implement covariance detail view (P1, phase: UX)
- #215: Implement sequential dashboard (P1, phase: UX)
- #216: Implement residual diagnostics panel (P1, phase: UX)
- #217: Implement refinement recipe wizard (P1, phase: UX)
- #218: Implement beginner guided workflow (P1, phase: UX)
- #219: Implement expert mode toggle (P1, phase: UX)
- #220: Implement report export UI (P1, phase: UX)
- #221: Implement provenance timeline UI (P1, phase: UX)
- #222: Implement keyboard command palette (P1, phase: UX)

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
