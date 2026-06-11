# Codex Prompt: AI and Agents Workstream

## Objective

Plan and implement a coherent sequence of issues in the **AI and Agents** workstream.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issues in this workstream

- #183: Define AI tool contract schema (P2, phase: AI)
- #184: Implement run_refinement tool wrapper (P2, phase: AI)
- #185: Implement diagnose_residuals tool wrapper (P2, phase: AI)
- #186: Implement set_refinement_flags tool wrapper (P2, phase: AI)
- #187: Implement rollback tool wrapper (P2, phase: AI)
- #188: Implement freeze_parameter tool wrapper (P2, phase: AI)
- #189: Implement add_constraint tool wrapper (P2, phase: AI)
- #190: Implement compare_models tool wrapper (P2, phase: AI)
- #191: Implement strategy rule engine v0 (P2, phase: AI)
- #192: Implement nonphysical solution detector (P2, phase: AI)
- #193: Implement overfitting detector (P2, phase: AI)
- #194: Implement residual pattern classifier skeleton (P2, phase: AI)
- #195: Implement agent action log viewer (P2, phase: AI)
- #196: Implement scientific copilot report generator (P2, phase: AI)
- #197: Implement AI safety policy checks (P2, phase: AI)
- #198: Implement AI evaluation benchmark suite (P2, phase: AI)
- #199: Implement prompt injection regression tests (P2, phase: AI)
- #200: Implement human approval checkpoint mechanism (P2, phase: AI)
- #201: Implement knowledge-base citation model (P2, phase: AI)
- #202: Implement autonomous recipe planner v0 (P2, phase: AI)

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
