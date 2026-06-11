# Codex Prompt: M11 Optimizer safeguard heuristics

## Objective

Implement the milestone `M11` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M11`
- Phase: `Optimization`
- Priority: `P1`
- Issue count: `2`

## Scope

Implement parameter-freezing and overparameterization diagnostics that protect autonomous workflows from nonphysical or underdetermined refinements.

## Mapped issues

- #82: Implement parameter-freezing heuristics (`Optimization`, P0)
- #83: Implement overparameterization detector (`Optimization`, P0)

## Dependencies

- M08
- M10

## Required deliverables

- parameter-freezing heuristics
- overparameterization detector

## Acceptance criteria

- Highly correlated or unstable parameters are flagged with explanations.
- Heuristics produce recommendations rather than silently changing the model.
- Diagnostics are covered by synthetic pathological cases.

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
