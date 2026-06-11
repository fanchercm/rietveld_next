# Codex Prompt: M27 EDXRD detector response and correction hooks

## Objective

Implement the milestone `M27` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M27`
- Phase: `Physics calculation`
- Priority: `P2`
- Issue count: `5`

## Scope

Implement the EDXRD detector response API, Gaussian response kernel, tail/escape hooks, and dead-time metadata.

## Mapped issues

- #156: Implement EDXRD detector response API (`EDXRD`, P2)
- #157: Implement Gaussian detector response kernel (`EDXRD`, P2)
- #158: Implement low-energy tail response hook (`EDXRD`, P2)
- #159: Implement escape peak correction hook (`EDXRD`, P2)
- #160: Implement dead-time correction metadata (`EDXRD`, P2)

## Dependencies

- M26
- M06

## Required deliverables

- detector response API
- Gaussian detector response kernel
- low-energy tail response hook
- escape peak correction hook
- dead-time correction metadata

## Acceptance criteria

- Detector response kernels are separable from crystallographic peak generation.
- Correction hooks are optional and provenance-recorded.
- Tests document current physical limitations.

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
