# Codex Prompt: M23 Magnetic entities and magnetic scattering foundation

## Objective

Implement the milestone `M23` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M23`
- Phase: `Physics calculation`
- Priority: `P1`
- Issue count: `3`

## Scope

Introduce magnetic moment, propagation-vector, and magnetic form-factor entities.

## Mapped issues

- #141: Implement magnetic moment entity (`Magnetic Refinement`, P2)
- #142: Implement propagation vector entity (`Magnetic Refinement`, P2)
- #143: Implement magnetic form-factor table (`Magnetic Refinement`, P2)

## Dependencies

- M13
- M18

## Required deliverables

- magnetic moment entity
- propagation vector entity
- magnetic form-factor table

## Acceptance criteria

- Magnetic entities are serializable in the core model.
- Magnetic form-factor lookup includes provenance metadata.
- Basic validation catches invalid moment definitions.

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
