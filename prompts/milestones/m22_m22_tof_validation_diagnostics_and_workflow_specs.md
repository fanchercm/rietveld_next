# Codex Prompt: M22 TOF validation diagnostics and workflow specs

## Objective

Implement the milestone `M22` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M22`
- Phase: `Physics calculation`
- Priority: `P2`
- Issue count: `5`

## Scope

Add TOF benchmarks, calibration workflow specification, diagnostics, event-mode provenance placeholder, and GSAS-II comparison fixture.

## Mapped issues

- #135: Implement TOF synthetic benchmark (`TOF`, P1)
- #136: Implement TOF calibration wizard spec (`TOF`, P1)
- #137: Implement TOF diagnostic plot data (`TOF`, P1)
- #138: Implement event-mode provenance placeholder (`TOF`, P1)
- #139: Implement GSAS-II TOF comparison fixture (`TOF`, P1)

## Dependencies

- M20
- M21

## Required deliverables

- TOF synthetic benchmark
- TOF calibration wizard spec
- TOF diagnostic plot data
- event-mode provenance placeholder
- GSAS-II TOF comparison fixture

## Acceptance criteria

- TOF benchmark is reproducible and not run in expensive mode by default.
- Calibration wizard spec maps GUI steps to API calls.
- Comparison fixture documents expected tolerances and limitations.

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
