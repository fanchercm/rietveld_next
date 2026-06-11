# Codex Prompt: Rietveld Next Program Execution Brief

You are implementing the next-generation Rietveld refinement platform described in this package.

## Canonical inputs

- `docs/report.md` is the technical design foundation.
- `backlog/issues.json` is the canonical issue backlog.
- `backlog/milestones.json` is the canonical milestone plan.
- `schemas/project.schema.json` is the current project schema.
- `architecture/src_layout_guardrails.md` defines source-layout constraints.
- `AGENTS.md` defines agent and automation conventions.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Working method

1. Pick exactly one milestone prompt or one issue prompt.
2. Read the mapped issue objects from `backlog/issues.json`.
3. Make the smallest coherent implementation increment.
4. Add or update tests, fixtures, schemas, docs, and examples as required by the prompt.
5. Preserve deterministic behavior and reproducibility.
6. Update documentation for every public API or workflow change.
7. Do not fabricate scientific validation; add fixtures and mark limitations honestly.

## Completion report

At the end of the Codex run, report:

- Files changed.
- Tests added or updated.
- Commands run.
- Any skipped acceptance criteria and why.
- Follow-up issues that should be opened.
