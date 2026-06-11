# AGENTS.md

Guidance for Codex, coding agents, and automation operating in this repository package.

## Project identity

Rietveld Next is a next-generation Rietveld refinement platform for X-ray, synchrotron, neutron, TOF, EDXRD, magnetic, texture, microstructure, high-throughput, AI-assisted, HPC, desktop, and web workflows.

## Canonical source-of-truth files

- `docs/report.md` — technical design document.
- `backlog/issues.json` — canonical granular issue backlog.
- `backlog/milestones.json` — canonical milestone plan.
- `github/issues_import.json` — GitHub issue import payloads.
- `github/milestones_import.json` — GitHub milestone import payloads.
- `schemas/project.schema.json` — project schema.
- `architecture/src_layout_guardrails.md` — source layout rules.
- `prompts/README.md` — prompt inventory and usage guidance.

## Non-negotiable source-layout rule

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

Before finishing any implementation task, verify that the repository does not contain forbidden top-level implementation directories.

## Agent operating rules

1. Work from a single issue prompt or milestone prompt unless explicitly asked to do program-level planning.
2. Read the corresponding issue objects in `backlog/issues.json` before editing.
3. Keep changes small, reviewable, and deterministic.
4. Preserve scientific auditability: record assumptions, units, schemas, tolerances, seeds, and provenance.
5. Do not invent validation results. If validation data is unavailable, create a placeholder fixture or document the limitation.
6. Do not make expensive benchmarks part of default CI unless specifically requested.
7. Prefer typed APIs, schema validation, and explicit error handling.
8. Keep user-facing and developer-facing documentation in sync with API changes.
9. Avoid duplicate frameworks, duplicate package trees, or parallel implementations that bypass existing boundaries.
10. Never silently change public file formats or schemas; version them.

## Scientific software expectations

- Numerical code must include shape, dtype, unit, and bounds validation where relevant.
- Refinement and optimization code must expose diagnostics and failure modes.
- Benchmarks must distinguish compile time, warmup time, and steady-state runtime.
- AI-agent code must call deterministic tools for numerical results and must log actions.
- All generated examples should be deterministic and reproducible.

## Testing expectations

For implementation PRs, add the smallest useful test set:

- Unit tests for pure logic.
- Schema round-trip tests for data model changes.
- Golden or synthetic-data tests for numerical kernels.
- Lightweight benchmark smoke tests for benchmark infrastructure.
- Documentation examples for public APIs.

Expensive validation, large benchmarks, or HPC tests must be opt-in.

## Documentation expectations

Update documentation when changing:

- Public APIs.
- File formats or schemas.
- Repository layout.
- Build or test commands.
- Scientific models or assumptions.
- Benchmark methodology.
- AI-agent behavior.

## Completion checklist for agents

Before reporting completion:

- Confirm all implementation source is under `src/`.
- Confirm tests or validation notes were added.
- Confirm acceptance criteria from the prompt are addressed.
- Confirm no duplicate issue or milestone files were introduced.
- Summarize files changed and commands run.
- Identify follow-up work honestly.
