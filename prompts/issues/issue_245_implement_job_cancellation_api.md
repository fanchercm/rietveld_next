# Codex Prompt: Issue #245 — Implement job cancellation API

## Objective

Complete GitHub issue `#245`: **Implement job cancellation API**.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issue metadata

- Category: `HPC and Cloud`
- Phase: `HPC`
- Priority: `P2`
- Labels: `hpc-and-cloud, hpc, p2, codex-ready, implementation`

## Dependencies

- ##1
- ##196

## Scope

Deliver a granular, testable increment for HPC and Cloud: Implement job cancellation API.

## Description

Implement or specify `Implement job cancellation API` as part of the next-generation Rietveld platform. Keep the change small, reviewable, and aligned with the `src/`-first repository layout.

## Required deliverables

- Source, schema, test, or documentation artifact for Implement job cancellation API
- Minimal developer-facing usage note
- Relevant test or validation fixture

## Acceptance criteria

- Implementation or document for `Implement job cancellation API` is placed under the approved `src/` layout or docs location; no forbidden top-level source directories are created.
- Public APIs, schemas, or commands introduced by the issue include minimal usage documentation.
- Automated tests or validation checks cover the primary success path and at least one failure or edge case.
- The change preserves deterministic behavior where randomness, ordering, or generated IDs are involved.
- CI-relevant commands complete without requiring large benchmarks, GPU hardware, or facility-only resources.
- The feature can be exercised locally with a mock or dry-run backend.
- Job metadata, environment, and result provenance are captured.

## Implementation instructions

1. Keep the change small enough for a focused pull request.
2. Prefer extending existing files and APIs over creating parallel duplicate implementations.
3. Add or update tests where the issue changes behavior.
4. Add docs or examples when the issue introduces a public interface or workflow.
5. Do not run expensive benchmarks or validation cases in default CI unless the issue explicitly requires it.
6. Keep generated artifacts deterministic.
7. Verify no forbidden top-level implementation directories were created.

## Final response requested from Codex

Report:

- Files changed.
- Tests run.
- Acceptance criteria satisfied.
- Remaining work or follow-up issues.
