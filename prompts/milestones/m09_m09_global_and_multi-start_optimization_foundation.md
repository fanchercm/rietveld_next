# Codex Prompt: M09 Global and multi-start optimization foundation

## Objective

Implement the milestone `M09` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M09`
- Phase: `Optimization`
- Priority: `P1`
- Issue count: `4`

## Scope

Implement initial global-search infrastructure for rugged refinement problems and autonomous starting-value discovery.

## Mapped issues

- #76: Implement differential evolution adapter (`Optimization`, P0)
- #77: Implement simulated annealing adapter (`Optimization`, P0)
- #78: Implement multi-start optimizer runner (`Optimization`, P0)
- #79: Implement Bayesian optimization placeholder API (`Optimization`, P0)

## Dependencies

- M08

## Required deliverables

- differential evolution adapter
- simulated annealing adapter
- multi-start runner
- Bayesian optimization placeholder API

## Acceptance criteria

- Global optimizers share a common result schema.
- Multi-start runs store seeds, candidates, objective values, and final local-refinement status.
- Expensive global tests are opt-in and excluded from normal CI.

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
