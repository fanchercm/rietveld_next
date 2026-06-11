# Codex Prompt: M28 EDXRD high-pressure validation and documentation

## Objective

Implement the milestone `M28` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M28`
- Phase: `Physics calculation`
- Priority: `P2`
- Issue count: `5`

## Scope

Add high-pressure entities, equation-of-state hook, synthetic benchmark, residual diagnostics, and user documentation example.

## Mapped issues

- #161: Implement high-pressure marker entity (`EDXRD`, P2)
- #162: Implement equation-of-state hook (`EDXRD`, P2)
- #163: Implement EDXRD synthetic benchmark (`EDXRD`, P2)
- #165: Implement EDXRD residual diagnostics (`EDXRD`, P2)
- #167: Implement EDXRD documentation example (`EDXRD`, P2)

## Dependencies

- M26
- M27

## Required deliverables

- high-pressure marker entity
- equation-of-state hook
- EDXRD synthetic benchmark
- EDXRD residual diagnostics
- EDXRD documentation example

## Acceptance criteria

- High-pressure marker metadata is represented in the project model.
- EDXRD benchmark writes reproducible results.
- Documentation walks through calibration and refinement assumptions.

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
