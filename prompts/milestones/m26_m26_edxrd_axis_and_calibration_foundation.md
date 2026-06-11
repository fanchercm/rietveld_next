# Codex Prompt: M26 EDXRD axis and calibration foundation

## Objective

Implement the milestone `M26` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M26`
- Phase: `Physics calculation`
- Priority: `P2`
- Issue count: `5`

## Scope

Implement energy-axis histograms, channel-to-energy calibration, fixed-angle Bragg conversion, EDXRD calibration workflow, and import template.

## Mapped issues

- #153: Implement energy-axis histogram model (`EDXRD`, P2)
- #154: Implement channel-to-energy calibration polynomial (`EDXRD`, P2)
- #155: Implement fixed-angle Bragg conversion (`EDXRD`, P2)
- #164: Implement EDXRD calibration workflow (`EDXRD`, P2)
- #166: Implement EDXRD import template (`EDXRD`, P2)

## Dependencies

- M13
- M15

## Required deliverables

- energy-axis histogram model
- channel-to-energy calibration polynomial
- fixed-angle Bragg conversion
- EDXRD calibration workflow
- EDXRD import template

## Acceptance criteria

- Energy-axis data can be represented without lossy conversion to 2theta.
- Calibration workflow stores coefficients and provenance.
- Fixed-angle conversion tests cover known standards.

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
