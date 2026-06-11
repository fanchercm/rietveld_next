# Codex Prompt: M05 Derivative and sparse Jacobian infrastructure

## Objective

Implement the milestone `M05` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M05`
- Phase: `Physics and numerical engine`
- Priority: `P0`
- Issue count: `5`

## Scope

Implement sparse Jacobian structures, finite-difference fallback, analytic derivatives for scale/background parameters, and gradient test utilities.

## Mapped issues

- #54: Implement sparse Jacobian data structure (`Numerical Engine`, P0)
- #55: Implement finite-difference Jacobian fallback (`Numerical Engine`, P0)
- #56: Implement analytic scale derivatives (`Numerical Engine`, P0)
- #57: Implement analytic background derivatives (`Numerical Engine`, P0)
- #69: Implement numerical gradient test utilities (`Numerical Engine`, P0)

## Dependencies

- M04

## Required deliverables

- sparse Jacobian data structure
- finite-difference derivative fallback
- analytic scale derivatives
- analytic background derivatives
- gradient verification utilities

## Acceptance criteria

- Sparse Jacobians preserve parameter-to-residual indexing.
- Analytic derivatives match finite differences within tolerance on synthetic cases.
- Gradient utilities produce actionable failure reports.

## Definition of done

- All mapped issues are closed or explicitly deferred with rationale.
- All implementation source created by this milestone is under src/.
- Public APIs, schemas, and generated artifacts are documented.
- Unit, integration, or validation tests relevant to the milestone pass in CI.
- Codex-facing notes include commands to reproduce validation or benchmark results.

## Implementation instructions

1. Read each mapped issue in `backlog/issues.json` before editing code.
2. Implement only the smallest coherent subset that satisfies this milestone.
3. Keep public APIs typed, documented, and testable.
4. Add lightweight tests that run in normal CI.
5. Put expensive scientific or performance checks behind explicit benchmark or validation commands.
6. Update relevant docs in `docs/`, `architecture/`, or `validation/` when behavior changes.
7. Preserve deterministic seeds and provenance for generated examples.

## Final response requested from Codex

Report:

- Completed issue numbers.
- Files changed.
- Tests and commands run.
- Acceptance criteria satisfied.
- Acceptance criteria not satisfied, if any.
