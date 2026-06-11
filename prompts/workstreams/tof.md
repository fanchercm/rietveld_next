# Codex Prompt: TOF Workstream

## Objective

Plan and implement a coherent sequence of issues in the **TOF** workstream.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issues in this workstream

- #126: Implement TOF histogram axis model (P1, phase: TOF)
- #127: Implement TOF detector bank entity (P1, phase: TOF)
- #128: Implement TOF calibration parameter set (P1, phase: TOF)
- #129: Implement DIFC-DIFA-zero peak position model (P1, phase: TOF)
- #130: Implement bank-specific background model (P1, phase: TOF)
- #131: Implement bank-specific profile parameter model (P1, phase: TOF)
- #132: Implement back-to-back exponential profile (P1, phase: TOF)
- #133: Implement TOF reflection windowing (P1, phase: TOF)
- #134: Implement multi-bank objective assembly (P1, phase: TOF)
- #135: Implement TOF synthetic benchmark (P1, phase: TOF)
- #136: Implement TOF calibration wizard spec (P1, phase: TOF)
- #137: Implement TOF diagnostic plot data (P1, phase: TOF)
- #138: Implement event-mode provenance placeholder (P1, phase: TOF)
- #139: Implement GSAS-II TOF comparison fixture (P1, phase: TOF)
- #140: Implement TOF bank mask handling (P1, phase: TOF)

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
