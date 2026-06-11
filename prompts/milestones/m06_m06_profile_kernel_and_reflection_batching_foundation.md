# Codex Prompt: M06 Profile kernel and reflection batching foundation

## Objective

Implement the milestone `M06` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M06`
- Phase: `Physics calculation`
- Priority: `P0`
- Issue count: `5`

## Scope

Implement core peak-profile kernels and execution planning needed for efficient profile calculation.

## Mapped issues

- #58: Implement Gaussian profile kernel (`Numerical Engine`, P0)
- #59: Implement pseudo-Voigt profile kernel (`Numerical Engine`, P0)
- #60: Implement Thompson-Cox-Hastings profile kernel (`Numerical Engine`, P0)
- #61: Implement peak window selection (`Numerical Engine`, P0)
- #62: Implement reflection batching plan (`Numerical Engine`, P0)

## Dependencies

- M04
- M05

## Required deliverables

- Gaussian profile kernel
- pseudo-Voigt profile kernel
- Thompson-Cox-Hastings profile kernel
- peak window selection
- reflection batching plan

## Acceptance criteria

- Each profile kernel has numerical tests and documented parameter conventions.
- Peak windowing excludes negligible contributions without changing results beyond tolerance.
- Reflection batching produces deterministic execution plans.

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
