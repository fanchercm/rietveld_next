# Codex Prompt: M29 Sequential and parametric workflow foundation

## Objective

Implement the milestone `M29` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M29`
- Phase: `Workflow`
- Priority: `P1`
- Issue count: `15`

## Scope

Implement sequential/parametric study execution, parameter evolution tables, and recipe plumbing.

## Mapped issues

- #168: Implement sequential runner (`Sequential and Parametric Workflows`, P1)
- #169: Implement sequential result table (`Sequential and Parametric Workflows`, P1)
- #170: Implement previous-point initialization (`Sequential and Parametric Workflows`, P1)
- #171: Implement failed-point retry policy (`Sequential and Parametric Workflows`, P1)
- #172: Implement parameter evolution export (`Sequential and Parametric Workflows`, P1)
- #173: Implement parametric model expression API (`Sequential and Parametric Workflows`, P1)
- #174: Implement temperature-dependent parameter model (`Sequential and Parametric Workflows`, P1)
- #175: Implement pressure-dependent parameter model (`Sequential and Parametric Workflows`, P1)
- #176: Implement sequential dashboard data API (`Sequential and Parametric Workflows`, P1)
- #177: Implement residual heatmap data export (`Sequential and Parametric Workflows`, P1)
- #178: Implement batch recipe format (`Sequential and Parametric Workflows`, P1)
- #179: Implement workflow replay command (`Sequential and Parametric Workflows`, P1)
- #180: Implement workflow checkpointing (`Sequential and Parametric Workflows`, P1)
- #181: Implement workflow comparison report (`Sequential and Parametric Workflows`, P1)
- #182: Implement high-throughput result summary (`Sequential and Parametric Workflows`, P1)

## Dependencies

- M15
- M08

## Required deliverables

- sequential runner
- parametric model API
- batch recipe integration
- study result tables
- workflow validation examples

## Acceptance criteria

- Sequential studies run deterministically on synthetic series.
- Parameter evolution tables include units, uncertainties, and provenance.
- Workflow recipes are scriptable and replayable.

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
