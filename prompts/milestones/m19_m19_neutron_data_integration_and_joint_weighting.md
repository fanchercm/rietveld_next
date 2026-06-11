# Codex Prompt: M19 Neutron data integration and joint weighting

## Objective

Implement the milestone `M19` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M19`
- Phase: `Physics calculation`
- Priority: `P1`
- Issue count: `5`

## Scope

Implement neutron-specific background, joint weighting, Mantid import, and uncertainty checks.

## Mapped issues

- #121: Implement container background model (`Neutron`, P1)
- #122: Implement neutron joint weighting model (`Neutron`, P1)
- #123: Implement nuclear neutron validation example (`Neutron`, P1)
- #124: Implement Mantid reduced-data import adapter (`Neutron`, P1)
- #125: Implement neutron uncertainty model checks (`Neutron`, P1)

## Dependencies

- M18

## Required deliverables

- container background model
- neutron joint weighting model
- nuclear neutron validation example
- Mantid reduced-data import adapter
- neutron uncertainty model checks

## Acceptance criteria

- Mantid reduced-data import handles at least one documented example shape.
- Joint weighting records likelihood/weighting assumptions.
- Validation example can be run from documentation.

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
