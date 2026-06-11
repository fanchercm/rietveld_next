# Codex Prompt: Optimization Workstream

## Objective

Plan and implement a coherent sequence of issues in the **Optimization** workstream.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issues in this workstream

- #71: Implement SciPy trust-region adapter (P0, phase: Engine)
- #72: Implement SciPy Levenberg-Marquardt adapter (P0, phase: Engine)
- #73: Implement Rust local optimizer trait (P0, phase: Engine)
- #74: Implement convergence report object (P0, phase: Engine)
- #75: Implement optimizer rollback snapshots (P0, phase: Engine)
- #76: Implement differential evolution adapter (P0, phase: Engine)
- #77: Implement simulated annealing adapter (P0, phase: Engine)
- #78: Implement multi-start optimizer runner (P0, phase: Engine)
- #79: Implement Bayesian optimization placeholder API (P0, phase: Engine)
- #80: Implement MCMC uncertainty API (P0, phase: Engine)
- #81: Implement optimizer result comparison utilities (P0, phase: Engine)
- #82: Implement parameter-freezing heuristics (P0, phase: Engine)
- #83: Implement overparameterization detector (P0, phase: Engine)
- #84: Implement model selection scoring interface (P0, phase: Engine)
- #85: Implement optimizer reproducibility seed management (P0, phase: Engine)

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
