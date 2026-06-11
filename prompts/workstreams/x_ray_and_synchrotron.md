# Codex Prompt: X-ray and Synchrotron Workstream

## Objective

Plan and implement a coherent sequence of issues in the **X-ray and Synchrotron** workstream.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issues in this workstream

- #106: Implement lab CW XRD instrument model (P1, phase: Scientific Models)
- #107: Implement synchrotron CW XRD instrument model (P1, phase: Scientific Models)
- #108: Implement wavelength metadata validation (P1, phase: Scientific Models)
- #109: Implement zero-shift calibration workflow (P1, phase: Scientific Models)
- #110: Implement fundamental-parameters API skeleton (P1, phase: Scientific Models)
- #111: Implement emission spectrum model skeleton (P1, phase: Scientific Models)
- #112: Implement axial divergence hook (P1, phase: Scientific Models)
- #113: Implement detector resolution hook (P1, phase: Scientific Models)
- #114: Implement 2D integration metadata link (P1, phase: Scientific Models)
- #115: Implement synchrotron beamline metadata template (P1, phase: Scientific Models)

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
