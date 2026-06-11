# Codex Prompt: Magnetic Refinement Workstream

## Objective

Plan and implement a coherent sequence of issues in the **Magnetic Refinement** workstream.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issues in this workstream

- #141: Implement magnetic moment entity (P2, phase: Magnetic)
- #142: Implement propagation vector entity (P2, phase: Magnetic)
- #143: Implement magnetic form-factor table (P2, phase: Magnetic)
- #144: Implement mCIF import skeleton (P2, phase: Magnetic)
- #145: Implement magnetic symmetry constraint API (P2, phase: Magnetic)
- #146: Implement representation-analysis import placeholder (P2, phase: Magnetic)
- #147: Implement nuclear-plus-magnetic phase coupling (P2, phase: Magnetic)
- #148: Implement magnetic reflection flagging (P2, phase: Magnetic)
- #149: Implement moment magnitude validation (P2, phase: Magnetic)
- #150: Implement magnetic refinement tutorial dataset stub (P2, phase: Magnetic)
- #151: Implement magnetic report section generator (P2, phase: Magnetic)
- #152: Implement magnetic parameter group recipes (P2, phase: Magnetic)

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
