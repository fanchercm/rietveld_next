# Codex Prompt: Architecture Workstream

## Objective

Plan and implement a coherent sequence of issues in the **Architecture** workstream.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issues in this workstream

- #1: Initialize src-first monorepo layout (P0, phase: Foundation)
- #2: Define workspace build conventions (P0, phase: Foundation)
- #3: Create package boundary document (P0, phase: Foundation)
- #4: Implement shared error taxonomy (P0, phase: Foundation)
- #5: Define plugin capability model (P0, phase: Foundation)
- #6: Create schema versioning policy (P0, phase: Foundation)
- #7: Implement configuration loading system (P0, phase: Foundation)
- #8: Define provenance event envelope (P0, phase: Foundation)
- #9: Implement environment capture module (P0, phase: Foundation)
- #10: Create architecture decision record workflow (P0, phase: Foundation)
- #11: Define public API stability levels (P0, phase: Foundation)
- #12: Implement feature flag registry (P0, phase: Foundation)
- #13: Create source layout linter (P0, phase: Foundation)
- #14: Define dependency boundary checks (P0, phase: Foundation)
- #15: Create release artifact manifest (P0, phase: Foundation)

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
