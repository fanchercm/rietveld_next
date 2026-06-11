# Codex Prompt: M24 Magnetic symmetry and import foundation

## Objective

Implement the milestone `M24` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M24`
- Phase: `Physics calculation`
- Priority: `P2`
- Issue count: `3`

## Scope

Create mCIF import skeleton, magnetic symmetry constraint API, and representation-analysis import placeholder.

## Mapped issues

- #144: Implement mCIF import skeleton (`Magnetic Refinement`, P2)
- #145: Implement magnetic symmetry constraint API (`Magnetic Refinement`, P2)
- #146: Implement representation-analysis import placeholder (`Magnetic Refinement`, P2)

## Dependencies

- M23

## Required deliverables

- mCIF import skeleton
- magnetic symmetry constraint API
- representation-analysis import placeholder

## Acceptance criteria

- mCIF import clearly reports supported and unsupported fields.
- Magnetic symmetry constraints are represented in the parameter graph.
- Representation-analysis placeholder includes documented extension contract.

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
