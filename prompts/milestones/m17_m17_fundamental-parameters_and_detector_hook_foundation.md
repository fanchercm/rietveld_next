# Codex Prompt: M17 Fundamental-parameters and detector hook foundation

## Objective

Implement the milestone `M17` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M17`
- Phase: `Physics calculation`
- Priority: `P2`
- Issue count: `5`

## Scope

Create extensible APIs for fundamental-parameters, emission spectra, axial divergence, detector resolution, and 2D integration metadata links.

## Mapped issues

- #110: Implement fundamental-parameters API skeleton (`X-ray and Synchrotron`, P1)
- #111: Implement emission spectrum model skeleton (`X-ray and Synchrotron`, P1)
- #112: Implement axial divergence hook (`X-ray and Synchrotron`, P1)
- #113: Implement detector resolution hook (`X-ray and Synchrotron`, P1)
- #114: Implement 2D integration metadata link (`X-ray and Synchrotron`, P1)

## Dependencies

- M16

## Required deliverables

- fundamental-parameters API skeleton
- emission spectrum model skeleton
- axial divergence hook
- detector resolution hook
- 2D integration metadata link

## Acceptance criteria

- Hooks are registered through the plugin/capability system.
- Skeleton implementations are documented as incomplete physics models.
- Tests verify that instrument hooks compose with the profile evaluation path.

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
