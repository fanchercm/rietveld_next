# Codex Prompt: M16 Lab and synchrotron CW X-ray instrument baseline

## Objective

Implement the milestone `M16` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M16`
- Phase: `Physics calculation`
- Priority: `P1`
- Issue count: `5`

## Scope

Implement lab and synchrotron CW X-ray instrument models and basic calibration/metadata validation workflows.

## Mapped issues

- #106: Implement lab CW XRD instrument model (`X-ray and Synchrotron`, P1)
- #107: Implement synchrotron CW XRD instrument model (`X-ray and Synchrotron`, P1)
- #108: Implement wavelength metadata validation (`X-ray and Synchrotron`, P1)
- #109: Implement zero-shift calibration workflow (`X-ray and Synchrotron`, P1)
- #115: Implement synchrotron beamline metadata template (`X-ray and Synchrotron`, P1)

## Dependencies

- M13
- M15

## Required deliverables

- lab CW XRD instrument model
- synchrotron CW XRD instrument model
- wavelength metadata validation
- zero-shift calibration workflow
- beamline metadata template

## Acceptance criteria

- Instrument models distinguish lab and synchrotron metadata.
- Zero-shift calibration is reproducible on a synthetic/reference case.
- Missing wavelength or beamline metadata produces actionable validation messages.

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
