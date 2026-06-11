# Rietveld Next Codex Package

This is the clean, prompt-expanded Codex package for the Rietveld Next software program.

## Start here

1. Read `AGENTS.md`.
2. Read `docs/report.md` for the technical design.
3. Use `prompts/README.md` to select a program, milestone, issue, or workstream prompt.
4. Use `backlog/issues.json` and `backlog/milestones.json` as the canonical backlog.

## Contents

- `backlog/issues.*` — canonical 327-issue backlog.
- `backlog/milestones.*` — canonical 40-milestone plan.
- `prompts/milestones/` — one prompt per milestone.
- `prompts/issues/` — one prompt per issue.
- `prompts/workstreams/` — one prompt per major workstream.
- `AGENTS.md` — operating instructions for coding agents.
- `schemas/` — project schema inputs.
- `architecture/` — architecture and source-layout guardrails.
- `github/` — import payloads.

## Source-layout rule

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `optimization/`, `benchmarks/`, or `tests/`.

## Batch-agent prompts

This package includes batch-agent prompts directly under `prompts/`:

- `prompts/00_universal_agent.md` through `prompts/29_optimization_batch.md`
- `prompts/BATCH_AGENT_PROMPTS.md`
- `prompts/VERIFY_BATCH_PROMPTS_00_10_PRESENT.txt`

The canonical package-tree document is `docs/PACKAGE_TREE.md`.
