# Rietveld Next Codex Input Pack

This package contains a Codex-ready decomposition of the technical design document for a next-generation Rietveld analysis platform.

## Contents

- `report/REPORT.md` - full technical report in Markdown.
- `sections/` - report split by major topic for targeted Codex work.
- `inputs/` - concise requirements, architecture inputs, repository tree, and implementation constraints.
- `prompts/` - ready-to-use prompts for Codex-driven implementation sessions.
- `schemas/project.schema.json` - starter schema for the project data model.
- `backlog/` - first milestones and first 100 GitHub issues.
- `adr/` - architecture decision records to seed a real repository.
- `repo_scaffold/` - repository tree and initial module boundary guidance.
- `evals/` - validation and benchmark plan for scientific and engineering quality.

## Suggested Codex workflow

1. Start with `prompts/00_codex_program_brief.md`.
2. Create the monorepo skeleton using `repo_scaffold/repo_tree.txt` and `inputs/repository_boundaries.md`.
3. Implement milestones from `backlog/milestones.md` in order.
4. Convert issues from `backlog/github_issues.md` or `backlog/github_issues.json` into GitHub issues.
5. Use `evals/validation_plan.md` as a release gate before publishing scientific features.

## Non-negotiable design constraints

- Every GUI action must map to a public API call.
- Every model mutation must be provenance-recorded.
- AI agents may recommend actions but numerical results must come from deterministic tools.
- The platform must support local, HPC, and cloud execution without changing project semantics.
- Scientific validation datasets and golden tests must be treated as first-class deliverables.

## 100-Milestone Implementation Plan

This bundle now includes a one-to-one 100-milestone implementation plan that maps each milestone to the corresponding seed GitHub issue:

- `backlog/milestones_100.md` — human-readable milestone plan
- `backlog/milestones_100.json` — canonical machine-readable milestone plan
- `backlog/milestones_100.csv` — spreadsheet/project-management import format
- `backlog/github_milestones_100.json` — GitHub milestone creation payloads
- `prompts/06_use_100_milestones.md` — Codex prompt for milestone-driven implementation



## Source layout

Implementation source code lives under `src/`. Codex should create source files under `src/<package>/...` and keep top-level `docs/`, `benchmarks/`, `examples/`, and `tests/` as support areas.
