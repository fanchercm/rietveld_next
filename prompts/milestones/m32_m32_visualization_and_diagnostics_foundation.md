# Codex Prompt: M32 Visualization and diagnostics foundation

## Objective

Implement the milestone `M32` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M32`
- Phase: `UX`
- Priority: `P1`
- Issue count: `10`

## Scope

Implement core visual diagnostics for profiles, correlations, residuals, sequential studies, and parameter graphs.

## Mapped issues

- #223: Implement profile plot data model (`Visualization`, P1)
- #224: Implement multi-bank plot aggregation (`Visualization`, P1)
- #225: Implement residual heatmap renderer (`Visualization`, P1)
- #226: Implement parameter evolution chart data (`Visualization`, P1)
- #227: Implement phase fraction evolution chart data (`Visualization`, P1)
- #228: Implement covariance matrix renderer (`Visualization`, P1)
- #229: Implement dependency graph renderer (`Visualization`, P1)
- #230: Implement reflection browser (`Visualization`, P1)
- #231: Implement mask and exclusion editor (`Visualization`, P1)
- #232: Implement publication figure export (`Visualization`, P1)

## Dependencies

- M07
- M29

## Required deliverables

- profile plots
- correlation heatmap
- residual diagnostics
- parameter graph visualization
- sequential dashboards

## Acceptance criteria

- Visual data payloads are testable without rendering.
- Plots distinguish observed, calculated, difference, and phase ticks.
- Correlation and residual warnings are linked to parameters.

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
