# Codex Prompt: Testing and Validation Workstream

## Objective

Plan and implement a coherent sequence of issues in the **Testing and Validation** workstream.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issues in this workstream

- #248: Create unit test conventions (P0, phase: Quality)
- #249: Create golden dataset format (P0, phase: Quality)
- #250: Create synthetic dataset generator tests (P0, phase: Quality)
- #251: Create scientific validation report template (P0, phase: Quality)
- #252: Add GSAS-II comparison test harness (P0, phase: Quality)
- #253: Add FullProf comparison placeholder (P0, phase: Quality)
- #254: Add TOPAS comparison placeholder (P0, phase: Quality)
- #255: Add numerical tolerance policy (P0, phase: Quality)
- #256: Add performance regression test harness (P0, phase: Quality)
- #257: Add cross-platform CI matrix (P0, phase: Quality)
- #258: Add package import smoke tests (P0, phase: Quality)
- #259: Add source layout guard test (P0, phase: Quality)
- #260: Add schema compatibility tests (P0, phase: Quality)
- #261: Add project round-trip tests (P0, phase: Quality)
- #262: Add benchmark result schema tests (P0, phase: Quality)
- #263: Add UX visual regression setup (P0, phase: Quality)
- #264: Add AI behavior regression tests (P0, phase: Quality)
- #265: Add security scanning workflow (P0, phase: Quality)
- #266: Add documentation link checker (P0, phase: Quality)
- #267: Add release validation checklist (P0, phase: Quality)

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
