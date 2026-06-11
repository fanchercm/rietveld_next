# Universal Agent Instructions for Rietveld Next

You are working in the `rietveld-next` repository.

## Canonical files

Before making changes, read:

- `AGENTS.md`
- `docs/PACKAGE_TREE.md`
- `backlog/issues.md`
- `backlog/milestones.md`
- Any issue-specific or milestone-specific prompt assigned to you

## Source layout rule

All implementation source code must live under `src/`.

Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`.

Documentation belongs under `docs/`. Prompt files belong under `prompts/`. Schemas belong under `schemas/`. Backlog files belong under `backlog/`. GitHub import files belong under `github/`.

## Safety rules

Do not perform broad rewrites. Do not rename public APIs unless the assigned issue explicitly requires it. Do not move large directory trees unless the assigned issue explicitly requires it. Do not modify unrelated workstreams. Do not change scientific formulas without adding tests and documentation. Do not introduce new dependencies without documenting why. Do not make expensive benchmarks run in normal CI. Do not claim scientific correctness unless validated by tests or references.

## Required behavior

Work only on your assigned issue or milestone. Preserve existing tests unless they are objectively wrong and the fix is documented. Add or update tests for every behavior change. Add or update documentation for public APIs, scientific formulas, benchmark behavior, or user-visible workflows. Keep changes small, reviewable, and scoped.

## Completion checklist

Before finishing, report:

1. Assigned issue or milestone.
2. Files changed.
3. Tests added or updated.
4. Commands run.
5. Any skipped work.
6. Any risks or follow-up issues.
7. Confirmation that all implementation code remains under `src/`.
