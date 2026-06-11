# Codex Prompt: Numerical Engine Workstream

## Objective

Plan and implement a coherent sequence of issues in the **Numerical Engine** workstream.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issues in this workstream

- #51: Implement residual vector interface (P0, phase: Engine)
- #52: Implement parameter scaling utilities (P0, phase: Engine)
- #53: Implement bounded parameter transforms (P0, phase: Engine)
- #54: Implement sparse Jacobian data structure (P0, phase: Engine)
- #55: Implement finite-difference Jacobian fallback (P0, phase: Engine)
- #56: Implement analytic scale derivatives (P0, phase: Engine)
- #57: Implement analytic background derivatives (P0, phase: Engine)
- #58: Implement Gaussian profile kernel (P0, phase: Engine)
- #59: Implement pseudo-Voigt profile kernel (P0, phase: Engine)
- #60: Implement Thompson-Cox-Hastings profile kernel (P0, phase: Engine)
- #61: Implement peak window selection (P0, phase: Engine)
- #62: Implement reflection batching plan (P0, phase: Engine)
- #63: Implement safe invalid-model handling (P0, phase: Engine)
- #64: Implement objective function registry (P0, phase: Engine)
- #65: Implement robust loss functions (P0, phase: Engine)
- #66: Implement Poisson likelihood objective (P0, phase: Engine)
- #67: Implement covariance calculation (P0, phase: Engine)
- #68: Implement correlation matrix calculation (P0, phase: Engine)
- #69: Implement numerical gradient test utilities (P0, phase: Engine)
- #70: Implement profile backend benchmark harness (P0, phase: Engine)

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
