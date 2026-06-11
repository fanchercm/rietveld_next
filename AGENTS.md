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

## Engineering Principles

1. Prefer clear, testable, maintainable code over clever code.
2. Separate scientific models from UI code.
3. Separate numerical kernels from workflow orchestration.
4. Keep APIs explicit and well documented.
5. Treat scientific reproducibility as a core feature.
6. Use versioned schemas for all persistent data.
7. Make performance measurable with benchmarks.
8. Require tests for all scientific calculations.
9. Prefer deterministic workflows unless stochastic behavior is explicitly required.
10. Document assumptions, approximations, and limitations.

---

## Scientific Principles

1. Never hide refinement assumptions from the user.
2. Preserve provenance for all data transformations.
3. Track parameter history during refinement.
4. Report uncertainty and parameter correlations where possible.
5. Warn users about underconstrained, unstable, or nonphysical refinements.
6. Support expert override while guiding novice users.
7. Prioritize physically meaningful results over numerical convergence alone.
8. Validate against known reference datasets and established software.

---

## Coding Standards

- Use typed APIs where practical.
- Prefer small, composable functions.
- Keep numerical kernels isolated and benchmarkable.
- Avoid global mutable state.
- Include docstrings for public functions.
- Include examples for public APIs.
- Use consistent naming for scientific concepts.
- Add regression tests for bug fixes.
- Add validation tests for scientific features.

---

## Testing Requirements

Every scientific feature should include:

- Unit tests
- Known-value tests
- Regression tests
- Cross-software comparison where possible
- Edge-case tests
- Performance tests if computationally intensive

Critical calculations requiring validation include:

- Peak positions
- Peak profiles
- Structure factors
- Background models
- Instrument models
- Least-squares refinement
- Constraints and restraints
- TOF profile functions
- EDXRD calibration functions
- Magnetic scattering models

---

## AI Usage Rules

AI agents may assist with:

- Code generation
- Refactoring
- Test generation
- Documentation
- Literature summaries
- UX proposals
- Workflow design
- Refinement strategy suggestions

AI agents must not:

- Invent scientific validation results
- Suppress uncertainty
- Hide failed tests
- Replace reference calculations without validation
- Make unverified claims about numerical correctness
- Change scientific behavior without tests

All AI-generated code must be reviewed, tested, and validated.

---

## Definition of Done

A feature is complete only when:

1. The scientific behavior is defined.
2. The implementation is tested.
3. The API is documented.
4. Example usage exists.
5. Validation data exists where applicable.
6. Performance has been measured where relevant.
7. Failure modes are documented.
8. The feature works in expected workflows.
9. The user-facing behavior is understandable.
10. The feature is reproducible.

---

## Priority Order

When tradeoffs arise, prioritize:

1. Scientific correctness
2. Reproducibility
3. Maintainability
4. Performance
5. UX quality
6. Extensibility
7. Automation
8. Convenience

---

## Long-Term Vision

This project should become a modern scientific operating system for diffraction analysis: a high-performance, AI-enabled, community-driven platform that transforms raw X-ray and neutron scattering measurements into validated scientific knowledge across laboratory, synchrotron, neutron facility, HPC, and autonomous experimental environments.

## 🎯 Core Principles

1. **Always assess before acting** — Understand the current state before proposing changes.
2. **Always provide itemized plans** — Break work into clear, testable steps tracked with `TodoWrite`.
3. **Focus on progress tracking** — The user should always know what's happening and what's next.
4. **Test incrementally** — Each step should be testable on its own.
5. **Review after major changes** — Delegate review to a sub-agent via the `Agent` tool.
6. **Ground truths** — ALWAYS record key findings in [docs/ground_truths.md](docs/ground_truths.md) for future reference. Update the file with new findings, and link to it from related documentation and code comments.


## 📝 Code Quality Standards

Always include:
1. **Type hints** on parameters and return values.
2. **Docstrings** — Google-style for public functions and classes.
3. **Specific exceptions** with clear messages.
4. **Input validation** at boundaries.
5. **Comments only when the WHY is non-obvious** — never narrate what the code does.

Example:

```python
from typing import Optional


def example_function(
    data: list[float],
    threshold: float = 0.5,
    normalize: bool = True,
) -> list[float]:
    """
    Process data with filtering and optional normalization.

    Args:
        data: Raw measurement values from sensor.
        threshold: Minimum value to keep (default: 0.5).
        normalize: Whether to normalize to [0, 1] range (default: True).

    Returns:
        Processed data values.

    Raises:
        ValueError: If data is empty or threshold is negative.

    Example:
        >>> example_function([0.1, 0.7, 1.2], threshold=0.5)
        [0.58, 1.0]
    """
    if not data:
        raise ValueError("Data cannot be empty")
    if threshold < 0:
        raise ValueError(f"Threshold must be non-negative, got {threshold}")

    filtered = [x for x in data if x >= threshold]
    if not filtered:
        return []

    if normalize:
        max_val = max(filtered)
        return [x / max_val for x in filtered]
    return filtered
```

Always cover:
1. **Normal cases** — typical inputs.
2. **Edge cases** — empty inputs, single items, max values.
3. **Error cases** — invalid inputs, type errors.
4. **Integration** — components working together.


## ⚡ Efficiency Guidelines

1. **Parallelize independent tool calls** — multiple `Read`/`Grep`/`Bash` calls go in one message when there are no dependencies.
2. **Use `Agent` with `subagent_type="Explore"`** for broad codebase exploration spanning more than ~3 queries; for narrower lookups, just use `Grep`/`Bash` directly.
3. **Prefer dedicated tools** — `Read`/`Edit`/`Write` over `cat`/`sed`/`echo` via `Bash`.
4. **Don't re-read files you just edited** — `Edit` errors if it failed.
5. **Give brief progress updates** at key moments — finding something, changing direction, hitting a blocker.
