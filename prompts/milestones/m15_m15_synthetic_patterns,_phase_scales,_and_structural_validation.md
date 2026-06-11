# Codex Prompt: M15 Synthetic patterns, phase scales, and structural validation

## Objective

Implement the milestone `M15` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M15`
- Phase: `Physics calculation`
- Priority: `P1`
- Issue count: `7`

## Scope

Create end-to-end synthetic pattern generation and phase quantification support with structural validation checks.

## Mapped issues

- #99: Implement reflection tick generation (`Diffraction Models`, P1)
- #100: Implement synthetic pattern generator (`Diffraction Models`, P1)
- #101: Implement standard reference dataset registry (`Diffraction Models`, P1)
- #102: Implement phase scale model (`Diffraction Models`, P1)
- #103: Implement phase fraction calculation (`Diffraction Models`, P1)
- #104: Implement atom occupancy constraints (`Diffraction Models`, P1)
- #105: Implement ADP validation checks (`Diffraction Models`, P1)

## Dependencies

- M12
- M13
- M14

## Required deliverables

- reflection tick generation
- synthetic pattern generator
- standard reference dataset registry
- phase scale model
- phase fraction calculation
- occupancy constraints
- ADP validation checks

## Acceptance criteria

- Synthetic patterns include phase ticks and metadata.
- Phase fraction calculation documents assumptions and normalization.
- Occupancy and ADP validation produce structured warnings.

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
