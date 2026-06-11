# Codex Prompt: Documentation and Governance Workstream

## Objective

Plan and implement a coherent sequence of issues in the **Documentation and Governance** workstream.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issues in this workstream

- #268: Write architecture overview (P1, phase: Governance)
- #269: Write src layout developer guide (P1, phase: Governance)
- #270: Write data model guide (P1, phase: Governance)
- #271: Write numerical engine theory guide (P1, phase: Governance)
- #272: Write optimization guide (P1, phase: Governance)
- #273: Write TOF refinement guide (P1, phase: Governance)
- #274: Write neutron refinement guide (P1, phase: Governance)
- #275: Write magnetic refinement guide (P1, phase: Governance)
- #276: Write EDXRD guide (P1, phase: Governance)
- #277: Write AI refinement guide (P1, phase: Governance)
- #278: Write HPC deployment guide (P1, phase: Governance)
- #279: Write plugin developer guide (P1, phase: Governance)
- #280: Write benchmark guide (P1, phase: Governance)
- #281: Write validation guide (P1, phase: Governance)
- #282: Write contribution guide (P1, phase: Governance)
- #283: Write code of conduct (P1, phase: Governance)
- #284: Write governance charter (P1, phase: Governance)
- #285: Write license and citation guide (P1, phase: Governance)
- #286: Write release process guide (P1, phase: Governance)
- #287: Write roadmap document (P1, phase: Governance)

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
