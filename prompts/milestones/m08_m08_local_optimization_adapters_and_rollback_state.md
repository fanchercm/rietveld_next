# Codex Prompt: M08 Local optimization adapters and rollback state

## Objective

Implement the milestone `M08` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M08`
- Phase: `Optimization`
- Priority: `P0`
- Issue count: `5`

## Scope

Implement local refinement infrastructure, including SciPy adapters, Rust optimizer trait, convergence reporting, and rollback snapshots.

## Mapped issues

- #71: Implement SciPy trust-region adapter (`Optimization`, P0)
- #72: Implement SciPy Levenberg-Marquardt adapter (`Optimization`, P0)
- #73: Implement Rust local optimizer trait (`Optimization`, P0)
- #74: Implement convergence report object (`Optimization`, P0)
- #75: Implement optimizer rollback snapshots (`Optimization`, P0)

## Dependencies

- M04
- M05

## Required deliverables

- trust-region adapter
- Levenberg-Marquardt adapter
- Rust optimizer trait
- convergence report object
- rollback snapshots

## Acceptance criteria

- A synthetic refinement runs through both local adapters where dependencies are available.
- Convergence reports include objective, iterations, termination reason, and parameter shifts.
- Rollback restores previous model state exactly.

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
