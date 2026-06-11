# Codex Prompt: M25 Magnetic joint-refinement validation and recipes

## Objective

Implement the milestone `M25` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M25`
- Phase: `Physics calculation`
- Priority: `P2`
- Issue count: `6`

## Scope

Implement nuclear-plus-magnetic coupling, magnetic reflection handling, validation, reports, and refinement recipes.

## Mapped issues

- #147: Implement nuclear-plus-magnetic phase coupling (`Magnetic Refinement`, P2)
- #148: Implement magnetic reflection flagging (`Magnetic Refinement`, P2)
- #149: Implement moment magnitude validation (`Magnetic Refinement`, P2)
- #150: Implement magnetic refinement tutorial dataset stub (`Magnetic Refinement`, P2)
- #151: Implement magnetic report section generator (`Magnetic Refinement`, P2)
- #152: Implement magnetic parameter group recipes (`Magnetic Refinement`, P2)

## Dependencies

- M23
- M24
- M19

## Required deliverables

- nuclear-plus-magnetic phase coupling
- magnetic reflection flagging
- moment magnitude validation
- tutorial dataset stub
- magnetic report section generator
- magnetic parameter group recipes

## Acceptance criteria

- Magnetic and nuclear contributions can be toggled and reported separately.
- Moment magnitude validation produces scientific warnings.
- Recipe docs explain safe staged magnetic refinement.

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
