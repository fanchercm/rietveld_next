# Rietveld Next Governance Guides

Purpose: provide concise governance documentation for issues #282-#287. These
sections describe how contributors should participate, release, cite, and plan
the project while preserving scientific auditability.

Current status: this is a project-level governance guide for a developing
research software prototype. It complements [AGENTS.md](../AGENTS.md),
[PACKAGE_TREE.md](PACKAGE_TREE.md), [prompts/23_documentation.md](../prompts/23_documentation.md),
[backlog/issues.json](../backlog/issues.json), and
[backlog/milestones.json](../backlog/milestones.json).

Non-goals: this guide is not legal advice, a replacement for a future formal
foundation charter, or evidence that every roadmap item is implemented.

## Contribution Guide

Scope: set expectations for small, reviewable, reproducible contributions.

Contribution workflow:

1. Pick one backlog issue or an explicitly scoped user request.
2. Read the related issue object in `../backlog/issues.json` before editing.
3. Confirm the owning package from [PACKAGE_TREE.md](PACKAGE_TREE.md).
4. Make the smallest deterministic change that satisfies the acceptance
   criteria.
5. Add package-local tests, documentation updates, or validation notes
   proportional to the change.
6. Run a focused validation command and record any skipped checks honestly.
7. Report files changed, commands run, limitations, and follow-up work.

Contribution standards:

- Put implementation source only under `../src/`.
- Use typed APIs, explicit validation, and specific exceptions.
- Document public APIs, schemas, commands, formulas, units, tolerances, seeds,
  and provenance when they affect scientific interpretation.
- Do not silently change persistent formats; version schema changes.
- Do not claim scientific validation from synthetic or smoke tests alone.
- Keep expensive benchmarks, GPU work, facility-only checks, and HPC jobs
  opt-in unless an issue explicitly requires them.

Runnable baseline command:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next -p 'test*.py'
```

Known limitations: review policy may become more formal as maintainers, release
branches, and protected checks are established.

## Code of Conduct

Scope: define behavior expected in project discussions, reviews, issues, and
scientific disagreement.

Expected behavior:

- Be respectful, specific, and evidence-oriented.
- Critique code, assumptions, validation evidence, and documentation without
  personal attacks.
- Treat uncertainty as normal in scientific software; ask for missing evidence
  rather than pressuring contributors to overclaim.
- Credit prior work, datasets, algorithms, and contributors.
- Respect maintainers' decisions about scope, reproducibility, and validation
  gates.
- Avoid harassment, discrimination, intimidation, doxxing, or sustained
  disruption.

Scientific conduct:

- Do not hide failed tests, failed refinements, missing validation, or unstable
  parameters.
- Do not present AI-generated output as validated numerical evidence.
- Do not remove provenance or warnings to make results look cleaner.
- Escalate suspected data-integrity, safety, license, or misconduct concerns to
  maintainers before broadening distribution.

Enforcement path:

1. Maintainers may ask for edits, clarification, or a pause in a discussion.
2. Serious or repeated violations may lead to issue moderation, review limits,
   temporary blocks, or removal from project spaces.
3. Maintainers should document enforcement decisions privately enough to protect
   reporters and publicly enough to keep project norms understandable.

Known limitations: the project may later adopt a named community code of
conduct. Until then, this section is the operative project guidance.

## Governance Charter

Scope: describe how decisions should be made while the project is evolving.

Decision principles, in priority order:

1. Scientific correctness.
2. Reproducibility.
3. Maintainability.
4. Performance.
5. UX quality.
6. Extensibility.
7. Automation.
8. Convenience.

Roles:

- Contributors propose changes through scoped issues, pull requests, docs, or
  validation artifacts.
- Maintainers guard architecture, schemas, releases, validation claims, and
  scientific scope.
- Domain reviewers evaluate scientific assumptions, formulas, reference data,
  and validation evidence.
- Automation agents may assist, but their output requires review and tests.

Decision records:

- Use architecture decision records for durable architecture, schema, storage,
  dependency, plugin, or governance choices.
- Include context, decision, alternatives, consequences, validation impact, and
  migration impact.
- Link decision records from affected docs or code comments when they govern
  behavior.

Conflict resolution:

- Prefer written proposals with concrete examples and validation evidence.
- If tradeoffs remain, maintainers choose the option that best satisfies the
  priority order above.
- Defer broad or speculative features when a smaller tested increment can move
  the project forward.

Known limitations: this charter does not define a voting body, steering
committee, or long-term funding model.

## License and Citation Guide

Scope: explain how to handle licensing and citation until formal release
metadata is finalized.

Contributor rules:

- Do not add code, datasets, reference tables, generated files, or copied text
  unless their license permits project use.
- Record source, license, version/date, and citation for scientific reference
  data.
- Keep third-party license notices with vendored or derived material.
- Prefer small metadata references over vendoring large external datasets.
- Ask maintainers before adding dependencies with restrictive, unclear, or
  incompatible licenses.

Citation expectations:

- Cite Rietveld Next when using project code, algorithms, or validation
  artifacts in publications once a formal citation is available.
- Cite underlying scientific methods, reference tables, external datasets, and
  comparison software separately.
- Include version, commit hash, input data provenance, and configuration when
  reporting refinement results.

Conceptual citation record:

```text
Software: Rietveld Next
Version: <release or commit hash>
Input package: <project package or dataset identifier>
Validation basis: <synthetic, reference dataset, or cross-software comparison>
External references: <methods, scattering tables, datasets, comparison tools>
```

Known limitations: this guide does not identify the repository's final license
text or publication DOI. Verify those artifacts before public release or
external redistribution.

## Release Process

Scope: define a conservative release checklist for a scientific prototype.

Release types:

- Development snapshot: useful for internal testing; may contain incomplete
  features and known validation gaps.
- Pre-release: intended for external feedback; must document limitations and
  migration risks.
- Stable release: requires documented APIs, schemas, validation status, release
  notes, and reproducible test results for supported workflows.

Release checklist:

1. Freeze scope to a milestone or explicit issue list.
2. Confirm no forbidden top-level implementation directories exist.
3. Run focused package tests and the repository-level lightweight test suite.
4. Run schema round-trip tests for persistent format changes.
5. Run benchmark smoke tests if benchmark infrastructure changed.
6. Update user/developer docs for public APIs, schemas, commands, assumptions,
   and limitations.
7. Write release notes with fixed issues, changed behavior, migration notes,
   validation status, known problems, and reproducibility metadata.
8. Tag the release only after tests, docs, and review evidence are recorded.

Recommended validation commands:

```bash
find . -maxdepth 1 -type d \( -name core -o -name diffraction -o -name xray -o -name neutron -o -name tof -o -name edxrd -o -name optimization -o -name workflows -o -name ai -o -name hpc -o -name desktop -o -name web -o -name benchmarks -o -name tests \) -print
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next -p 'test*.py'
```

Known limitations: final packaging, artifact signing, DOI publication, and
long-term support policy are not yet specified in this guide.

## Roadmap

Scope: summarize planning direction without replacing the canonical backlog and
milestone files.

Canonical planning files:

- `../backlog/issues.json` is the granular issue backlog.
- `../backlog/milestones.json` is the milestone plan.
- `../github/issues_import.json` and `../github/milestones_import.json` are
  import payloads derived from backlog state.
- `../prompts/` contains program, milestone, workstream, and issue prompts.

Roadmap themes:

- Foundation: preserve the `src/`-first architecture, typed core model,
  schema-backed serialization, package storage, provenance, and guardrails.
- Physics: expand validated diffraction, structure, X-ray, neutron, TOF,
  EDXRD, magnetic, texture, and microstructure calculations.
- Optimization: strengthen local/global optimization, uncertainty reporting,
  diagnostics, rollback, and model-comparison workflows.
- Workflows: support reproducible sequential studies, batch analysis,
  autonomous experiments, and high-throughput execution.
- Interfaces: develop desktop, web, visualization, plugin, and AI-assisted
  workflows without bypassing deterministic numerical APIs.
- Validation: grow reference datasets, cross-software comparisons, benchmark
  harnesses, and publication-quality reporting.
- Operations: mature governance, release, citation, documentation, security,
  and contributor processes.

Planning rules:

- The backlog is canonical; roadmap summaries must not create hidden scope.
- Roadmap items should state dependencies, validation needs, and known
  limitations.
- Scientific validation gates should be explicit before a feature is described
  as complete.
- Expensive validation and HPC work should be planned as opt-in jobs with
  reproducible inputs and outputs.

Known limitations: priorities may change as validation gaps, contributor
capacity, and real instrument data become clearer.
