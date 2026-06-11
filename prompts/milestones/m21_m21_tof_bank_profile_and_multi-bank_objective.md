# Codex Prompt: M21 TOF bank profile and multi-bank objective

## Objective

Implement the milestone `M21` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M21`
- Phase: `Physics calculation`
- Priority: `P1`
- Issue count: `5`

## Scope

Implement bank-specific backgrounds, profile parameters, back-to-back exponential profiles, TOF windowing, and multi-bank objective assembly.

## Mapped issues

- #130: Implement bank-specific background model (`TOF`, P1)
- #131: Implement bank-specific profile parameter model (`TOF`, P1)
- #132: Implement back-to-back exponential profile (`TOF`, P1)
- #133: Implement TOF reflection windowing (`TOF`, P1)
- #134: Implement multi-bank objective assembly (`TOF`, P1)

## Dependencies

- M20
- M06

## Required deliverables

- bank-specific background model
- bank-specific profile parameter model
- back-to-back exponential profile
- TOF reflection windowing
- multi-bank objective assembly

## Acceptance criteria

- Each bank can refine local profile/background parameters while sharing phase parameters.
- Back-to-back exponential tests verify asymmetry and normalization behavior.
- Multi-bank objective returns labeled residual blocks.

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
