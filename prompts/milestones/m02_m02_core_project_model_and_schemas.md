# Codex Prompt: M02 Core project model and schemas

## Objective

Implement the milestone `M02` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M02`
- Phase: `Foundation`
- Priority: `P0`
- Issue count: `20`

## Scope

Define typed project, experiment, dataset, histogram, phase, parameter, constraint, strategy, and sequential-study models.

## Mapped issues

- #16: Define Project entity (`Core Data Model`, P0)
- #17: Define Experiment entity (`Core Data Model`, P0)
- #18: Define Dataset entity (`Core Data Model`, P0)
- #19: Define Histogram entity (`Core Data Model`, P0)
- #20: Define Instrument entity (`Core Data Model`, P0)
- #21: Define DetectorBank entity (`Core Data Model`, P0)
- #22: Define Phase entity (`Core Data Model`, P0)
- #23: Define CrystalStructure entity (`Core Data Model`, P0)
- #24: Define MagneticStructure entity (`Core Data Model`, P0)
- #25: Define RefinementParameter entity (`Core Data Model`, P0)
- #26: Define Constraint entity (`Core Data Model`, P0)
- #27: Define OptimizationStrategy entity (`Core Data Model`, P0)
- #28: Define SequentialStudy entity (`Core Data Model`, P0)
- #29: Implement parameter path addressing (`Core Data Model`, P0)
- #30: Implement typed units metadata (`Core Data Model`, P0)
- #31: Implement bounds and priors metadata (`Core Data Model`, P0)
- #32: Implement entity ID validation (`Core Data Model`, P0)
- #33: Implement model graph serialization (`Core Data Model`, P0)
- #34: Implement model graph diffing (`Core Data Model`, P0)
- #35: Implement model graph migration harness (`Core Data Model`, P0)

## Dependencies

- M01

## Required deliverables

- core JSON schemas
- Rust/Python domain objects
- parameter ownership model
- constraint references
- schema round-trip tests

## Acceptance criteria

- All core entities serialize and deserialize deterministically.
- Schema validation rejects malformed project files.
- Parameter paths are stable and documented.
- Core model tests pass.

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
