# Codex Prompt: M12 Structural IO and symmetry baseline

## Objective

Implement the milestone `M12` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M12`
- Phase: `Physics calculation`
- Priority: `P0`
- Issue count: `4`

## Scope

Implement CIF ingestion, validation reporting, space-group lookup, and reflection generation.

## Mapped issues

- #86: Implement CIF import v0 (`Diffraction Models`, P1)
- #87: Implement CIF validation report (`Diffraction Models`, P1)
- #88: Implement space-group lookup service (`Diffraction Models`, P1)
- #89: Implement reflection generation service (`Diffraction Models`, P1)

## Dependencies

- M02

## Required deliverables

- CIF import v0
- CIF validation report
- space-group lookup service
- reflection generation service

## Acceptance criteria

- Representative CIFs import successfully.
- Validation reports identify missing/ambiguous crystallographic fields.
- Reflection generation matches reference cases for simple space groups.

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
