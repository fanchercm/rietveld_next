# Codex Prompt: Core Data Model Workstream

## Objective

Plan and implement a coherent sequence of issues in the **Core Data Model** workstream.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issues in this workstream

- #16: Define Project entity (P0, phase: Foundation)
- #17: Define Experiment entity (P0, phase: Foundation)
- #18: Define Dataset entity (P0, phase: Foundation)
- #19: Define Histogram entity (P0, phase: Foundation)
- #20: Define Instrument entity (P0, phase: Foundation)
- #21: Define DetectorBank entity (P0, phase: Foundation)
- #22: Define Phase entity (P0, phase: Foundation)
- #23: Define CrystalStructure entity (P0, phase: Foundation)
- #24: Define MagneticStructure entity (P0, phase: Foundation)
- #25: Define RefinementParameter entity (P0, phase: Foundation)
- #26: Define Constraint entity (P0, phase: Foundation)
- #27: Define OptimizationStrategy entity (P0, phase: Foundation)
- #28: Define SequentialStudy entity (P0, phase: Foundation)
- #29: Implement parameter path addressing (P0, phase: Foundation)
- #30: Implement typed units metadata (P0, phase: Foundation)
- #31: Implement bounds and priors metadata (P0, phase: Foundation)
- #32: Implement entity ID validation (P0, phase: Foundation)
- #33: Implement model graph serialization (P0, phase: Foundation)
- #34: Implement model graph diffing (P0, phase: Foundation)
- #35: Implement model graph migration harness (P0, phase: Foundation)

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
