# Codex Prompt: Issue #251 — Create scientific validation report template

## Objective

Complete GitHub issue `#251`: **Create scientific validation report template**.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issue metadata

- Category: `Testing and Validation`
- Phase: `Quality`
- Priority: `P0`
- Labels: `testing-and-validation, quality, p0, codex-ready, design`

## Dependencies

- ##1

## Scope

Deliver a granular, testable increment for Testing and Validation: Create scientific validation report template.

## Description

Implement or specify `Create scientific validation report template` as part of the next-generation Rietveld platform. Keep the change small, reviewable, and aligned with the `src/`-first repository layout.

## Required deliverables

- Source, schema, test, or documentation artifact for Create scientific validation report template
- Minimal developer-facing usage note
- Relevant test or validation fixture

## Acceptance criteria

- Implementation or document for `Create scientific validation report template` is placed under the approved `src/` layout or docs location; no forbidden top-level source directories are created.
- Public APIs, schemas, or commands introduced by the issue include minimal usage documentation.
- Automated tests or validation checks cover the primary success path and at least one failure or edge case.
- The change preserves deterministic behavior where randomness, ordering, or generated IDs are involved.
- CI-relevant commands complete without requiring large benchmarks, GPU hardware, or facility-only resources.

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
