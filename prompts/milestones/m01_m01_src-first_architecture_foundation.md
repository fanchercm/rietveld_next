# Codex Prompt: M01 Src-first architecture foundation

## Objective

Implement the milestone `M01` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M01`
- Phase: `Foundation`
- Priority: `P0`
- Issue count: `15`

## Scope

Establish the repository, source-layout guardrails, package boundaries, plugin capability model, and architecture decision workflow.

## Mapped issues

- #1: Initialize src-first monorepo layout (`Architecture`, P0)
- #2: Define workspace build conventions (`Architecture`, P0)
- #3: Create package boundary document (`Architecture`, P0)
- #4: Implement shared error taxonomy (`Architecture`, P0)
- #5: Define plugin capability model (`Architecture`, P0)
- #6: Create schema versioning policy (`Architecture`, P0)
- #7: Implement configuration loading system (`Architecture`, P0)
- #8: Define provenance event envelope (`Architecture`, P0)
- #9: Implement environment capture module (`Architecture`, P0)
- #10: Create architecture decision record workflow (`Architecture`, P0)
- #11: Define public API stability levels (`Architecture`, P0)
- #12: Implement feature flag registry (`Architecture`, P0)
- #13: Create source layout linter (`Architecture`, P0)
- #14: Define dependency boundary checks (`Architecture`, P0)
- #15: Create release artifact manifest (`Architecture`, P0)

## Dependencies

- None

## Required deliverables

- src-first monorepo scaffold
- workspace/build conventions
- package boundary document
- shared error taxonomy
- plugin capability model
- architecture decision record template

## Acceptance criteria

- Repository has no forbidden top-level implementation directories.
- Build and lint commands are documented.
- Package boundaries are explicit and enforceable.
- Architecture decision records can be created and reviewed.

## Definition of done

- All mapped issues are closed or explicitly deferred with rationale.
- All implementation source created by this milestone is under src/.
- Public APIs, schemas, and generated artifacts are documented.
- Unit, integration, or validation tests relevant to the milestone pass in CI.
- Codex-facing notes include commands to reproduce validation or benchmark results.

## Implementation instructions

1. Read each mapped issue in `backlog/issues.json` before editing code.
2. Implement only the smallest coherent subset that satisfies this milestone.
3. Keep public APIs typed, documented, and testable.
4. Add lightweight tests that run in normal CI.
5. Put expensive scientific or performance checks behind explicit benchmark or validation commands.
6. Update relevant docs in `docs/`, `architecture/`, or `validation/` when behavior changes.
7. Preserve deterministic seeds and provenance for generated examples.

## Final response requested from Codex

Report:

- Completed issue numbers.
- Files changed.
- Tests and commands run.
- Acceptance criteria satisfied.
- Acceptance criteria not satisfied, if any.
