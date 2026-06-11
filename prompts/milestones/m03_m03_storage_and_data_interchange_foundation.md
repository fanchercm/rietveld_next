# Codex Prompt: M03 Storage and data interchange foundation

## Objective

Implement the milestone `M03` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M03`
- Phase: `Foundation`
- Priority: `P0`
- Issue count: `15`

## Scope

Create the project package, storage adapters, provenance log, and baseline data interchange paths.

## Mapped issues

- #36: Create Rietveld project package reader (`Storage and IO`, P0)
- #37: Create Rietveld project package writer (`Storage and IO`, P0)
- #38: Implement JSON schema validation CLI (`Storage and IO`, P0)
- #39: Implement NeXus file reference model (`Storage and IO`, P0)
- #40: Implement HDF5 metadata adapter (`Storage and IO`, P0)
- #41: Implement Zarr profile-array adapter (`Storage and IO`, P0)
- #42: Implement Parquet result-table writer (`Storage and IO`, P0)
- #43: Implement Arrow parameter-table export (`Storage and IO`, P0)
- #44: Implement JSONL provenance log writer (`Storage and IO`, P0)
- #45: Implement project package integrity checker (`Storage and IO`, P0)
- #46: Implement data URI resolver (`Storage and IO`, P0)
- #47: Implement checksum and file manifest support (`Storage and IO`, P0)
- #48: Implement import warning report format (`Storage and IO`, P0)
- #49: Implement project compression option (`Storage and IO`, P0)
- #50: Implement round-trip storage regression tests (`Storage and IO`, P0)

## Dependencies

- M02

## Required deliverables

- project package layout
- JSONL provenance
- NeXus/HDF5 references
- Zarr/Parquet/Arrow adapter stubs
- import/export tests

## Acceptance criteria

- Project packages can be created, opened, and validated.
- Large array references are not embedded in JSON metadata.
- Provenance actions are append-only and replayable in tests.
- Storage documentation covers local and cloud usage.

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
