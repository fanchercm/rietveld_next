# Codex Prompt: EDXRD Workstream

## Objective

Plan and implement a coherent sequence of issues in the **EDXRD** workstream.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issues in this workstream

- #153: Implement energy-axis histogram model (P2, phase: EDXRD)
- #154: Implement channel-to-energy calibration polynomial (P2, phase: EDXRD)
- #155: Implement fixed-angle Bragg conversion (P2, phase: EDXRD)
- #156: Implement EDXRD detector response API (P2, phase: EDXRD)
- #157: Implement Gaussian detector response kernel (P2, phase: EDXRD)
- #158: Implement low-energy tail response hook (P2, phase: EDXRD)
- #159: Implement escape peak correction hook (P2, phase: EDXRD)
- #160: Implement dead-time correction metadata (P2, phase: EDXRD)
- #161: Implement high-pressure marker entity (P2, phase: EDXRD)
- #162: Implement equation-of-state hook (P2, phase: EDXRD)
- #163: Implement EDXRD synthetic benchmark (P2, phase: EDXRD)
- #164: Implement EDXRD calibration workflow (P2, phase: EDXRD)
- #165: Implement EDXRD residual diagnostics (P2, phase: EDXRD)
- #166: Implement EDXRD import template (P2, phase: EDXRD)
- #167: Implement EDXRD documentation example (P2, phase: EDXRD)

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
