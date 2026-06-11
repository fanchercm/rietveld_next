# Architecture Decision Record Workflow

Architecture decisions are recorded under `architecture/` as Markdown files.
Use `architecture/0000-adr-template.md` when proposing a new decision.

## Status Values

- `Proposed`: under discussion and not yet binding.
- `Accepted`: current project direction.
- `Deprecated`: retained for history but no longer recommended.
- `Superseded`: replaced by a newer ADR.

## Required Sections

Each Architecture Decision Record must include:

- Title
- Status
- Date
- Context
- Decision
- Consequences
- Validation
- Provenance

## Review Rules

- ADRs must not contradict `AGENTS.md`, `docs/PACKAGE_TREE.md`, or
  `architecture/src_layout_guardrails.md`.
- Decisions that change public file formats or schemas must describe migration
  impact.
- Decisions that affect scientific behavior must identify tests, validation
  data, or explicit limitations.
- Decisions that introduce dependencies must state why existing dependencies
  are insufficient.

## Validation Command

Run architecture tests before accepting ADRs that affect package layout or
dependency direction:

```bash
PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next/core/architecture
```
