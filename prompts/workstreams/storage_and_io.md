# Codex Prompt: Storage and IO Workstream

## Objective

Plan and implement a coherent sequence of issues in the **Storage and IO** workstream.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issues in this workstream

- #36: Create Rietveld project package reader (P0, phase: Foundation)
- #37: Create Rietveld project package writer (P0, phase: Foundation)
- #38: Implement JSON schema validation CLI (P0, phase: Foundation)
- #39: Implement NeXus file reference model (P0, phase: Foundation)
- #40: Implement HDF5 metadata adapter (P0, phase: Foundation)
- #41: Implement Zarr profile-array adapter (P0, phase: Foundation)
- #42: Implement Parquet result-table writer (P0, phase: Foundation)
- #43: Implement Arrow parameter-table export (P0, phase: Foundation)
- #44: Implement JSONL provenance log writer (P0, phase: Foundation)
- #45: Implement project package integrity checker (P0, phase: Foundation)
- #46: Implement data URI resolver (P0, phase: Foundation)
- #47: Implement checksum and file manifest support (P0, phase: Foundation)
- #48: Implement import warning report format (P0, phase: Foundation)
- #49: Implement project compression option (P0, phase: Foundation)
- #50: Implement round-trip storage regression tests (P0, phase: Foundation)

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
