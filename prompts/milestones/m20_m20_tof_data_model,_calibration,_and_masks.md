# Codex Prompt: M20 TOF data model, calibration, and masks

## Objective

Implement the milestone `M20` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M20`
- Phase: `Physics calculation`
- Priority: `P1`
- Issue count: `5`

## Scope

Implement TOF histogram axis, detector bank model, calibration parameter set, DIFC/DIFA/zero peak positions, and bank masks.

## Mapped issues

- #126: Implement TOF histogram axis model (`TOF`, P1)
- #127: Implement TOF detector bank entity (`TOF`, P1)
- #128: Implement TOF calibration parameter set (`TOF`, P1)
- #129: Implement DIFC-DIFA-zero peak position model (`TOF`, P1)
- #140: Implement TOF bank mask handling (`TOF`, P1)

## Dependencies

- M18

## Required deliverables

- TOF histogram axis model
- TOF detector bank entity
- TOF calibration parameter set
- DIFC-DIFA-zero peak position model
- TOF bank mask handling

## Acceptance criteria

- Multi-bank projects can represent independent bank calibration parameters.
- Peak-position tests cover at least two banks.
- Bank masks propagate into residual calculation.

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
