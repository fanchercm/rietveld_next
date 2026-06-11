# Codex Prompt: M07 Uncertainty diagnostics and profile benchmark harness

## Objective

Implement the milestone `M07` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M07`
- Phase: `Physics and numerical engine`
- Priority: `P1`
- Issue count: `3`

## Scope

Implement covariance/correlation diagnostics and the first backend benchmark harness for profile calculations.

## Mapped issues

- #67: Implement covariance calculation (`Numerical Engine`, P0)
- #68: Implement correlation matrix calculation (`Numerical Engine`, P0)
- #70: Implement profile backend benchmark harness (`Numerical Engine`, P0)

## Dependencies

- M05
- M06

## Required deliverables

- covariance calculation
- correlation matrix calculation
- profile backend benchmark harness

## Acceptance criteria

- Covariance and correlation outputs include parameter labels and units.
- Singular or ill-conditioned cases return warnings rather than misleading uncertainties.
- Benchmark results are machine-readable and reproducible.

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
