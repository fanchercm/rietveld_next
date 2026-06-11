# Codex Prompt: Issue #272 — Write optimization guide

## Objective

Complete GitHub issue `#272`: **Write optimization guide**.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issue metadata

- Category: `Documentation and Governance`
- Phase: `Governance`
- Priority: `P1`
- Labels: `documentation-and-governance, governance, p1, codex-ready, documentation`

## Dependencies

- ##1

## Scope

Deliver a granular, testable increment for Documentation and Governance: Write optimization guide.

## Description

Implement or specify `Write optimization guide` as part of the next-generation Rietveld platform. Keep the change small, reviewable, and aligned with the `src/`-first repository layout.

## Required deliverables

- Source, schema, test, or documentation artifact for Write optimization guide
- Minimal developer-facing usage note
- Relevant test or validation fixture

## Acceptance criteria

- Implementation or document for `Write optimization guide` is placed under the approved `src/` layout or docs location; no forbidden top-level source directories are created.
- Public APIs, schemas, or commands introduced by the issue include minimal usage documentation.
- Automated tests or validation checks cover the primary success path and at least one failure or edge case.
- The change preserves deterministic behavior where randomness, ordering, or generated IDs are involved.
- CI-relevant commands complete without requiring large benchmarks, GPU hardware, or facility-only resources.
- Documentation includes purpose, scope, non-goals, examples, and links to related files.
- The document is written so a new contributor or Codex agent can act on it without additional context.

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
