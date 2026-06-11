# Codex Prompt: HPC and Cloud Workstream

## Objective

Plan and implement a coherent sequence of issues in the **HPC and Cloud** workstream.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issues in this workstream

- #233: Implement local parallel batch runner (P2, phase: HPC)
- #234: Implement scheduler abstraction (P2, phase: HPC)
- #235: Implement Slurm job-array adapter (P2, phase: HPC)
- #236: Implement Slurm result collector (P2, phase: HPC)
- #237: Implement Dask adapter skeleton (P2, phase: HPC)
- #238: Implement Ray adapter skeleton (P2, phase: HPC)
- #239: Implement Kubernetes worker manifest (P2, phase: HPC)
- #240: Implement object storage URI abstraction (P2, phase: HPC)
- #241: Implement distributed result database writer (P2, phase: HPC)
- #242: Implement benchmark cluster smoke test (P2, phase: HPC)
- #243: Implement beamline live-ingest mock (P2, phase: HPC)
- #244: Implement real-time status stream (P2, phase: HPC)
- #245: Implement job cancellation API (P2, phase: HPC)
- #246: Implement retry and backoff policy (P2, phase: HPC)
- #247: Implement HPC provenance capture (P2, phase: HPC)

## Execution guidance

- Start with P0 issues and dependency-free issues.
- Prefer milestone prompts for multi-issue implementation.
- Prefer individual issue prompts for targeted pull requests.
- Keep scientific claims tied to tests, fixtures, or documentation.
- Avoid broad rewrites unless an issue explicitly requires an architecture change.

## Final response requested from Codex

Report:

- Issues completed.
- Issues partially completed.
- Tests and validation commands run.
- Follow-up issue recommendations.
