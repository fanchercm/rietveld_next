# Codex Prompt: M14 Orientation, microstructure, and background models

## Objective

Implement the milestone `M14` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M14`
- Phase: `Physics calculation`
- Priority: `P1`
- Issue count: `5`

## Scope

Implement first-generation preferred-orientation, size/strain broadening, and polynomial/Chebyshev background models.

## Mapped issues

- #94: Implement preferred orientation model v0 (`Diffraction Models`, P1)
- #95: Implement isotropic size broadening (`Diffraction Models`, P1)
- #96: Implement isotropic strain broadening (`Diffraction Models`, P1)
- #97: Implement background polynomial model (`Diffraction Models`, P1)
- #98: Implement Chebyshev background model (`Diffraction Models`, P1)

## Dependencies

- M06
- M13

## Required deliverables

- preferred orientation model v0
- isotropic size broadening
- isotropic strain broadening
- polynomial background model
- Chebyshev background model

## Acceptance criteria

- Each model has parameter bounds and validation rules.
- Background models can be refined independently from phase/profile parameters.
- Size and strain contributions are separately testable on synthetic patterns.

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
