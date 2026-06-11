# Codex Prompt: M33 HPC and cloud execution foundation

## Objective

Implement the milestone `M33` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M33`
- Phase: `HPC`
- Priority: `P1`
- Issue count: `15`

## Scope

Implement local, Slurm, Dask/Ray, Kubernetes, and result-store execution foundations.

## Mapped issues

- #233: Implement local parallel batch runner (`HPC and Cloud`, P2)
- #234: Implement scheduler abstraction (`HPC and Cloud`, P2)
- #235: Implement Slurm job-array adapter (`HPC and Cloud`, P2)
- #236: Implement Slurm result collector (`HPC and Cloud`, P2)
- #237: Implement Dask adapter skeleton (`HPC and Cloud`, P2)
- #238: Implement Ray adapter skeleton (`HPC and Cloud`, P2)
- #239: Implement Kubernetes worker manifest (`HPC and Cloud`, P2)
- #240: Implement object storage URI abstraction (`HPC and Cloud`, P2)
- #241: Implement distributed result database writer (`HPC and Cloud`, P2)
- #242: Implement benchmark cluster smoke test (`HPC and Cloud`, P2)
- #243: Implement beamline live-ingest mock (`HPC and Cloud`, P2)
- #244: Implement real-time status stream (`HPC and Cloud`, P2)
- #245: Implement job cancellation API (`HPC and Cloud`, P2)
- #246: Implement retry and backoff policy (`HPC and Cloud`, P2)
- #247: Implement HPC provenance capture (`HPC and Cloud`, P2)

## Dependencies

- M29

## Required deliverables

- local batch runner
- Slurm adapter
- Dask adapter
- Ray adapter
- Kubernetes worker prototype
- result store

## Acceptance criteria

- Local batch execution handles synthetic ensembles.
- Scheduler adapters have fake/local tests.
- Result records are reproducible and portable.

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
