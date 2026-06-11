# Codex Prompt: M10 Probabilistic uncertainty and model comparison foundation

## Objective

Implement the milestone `M10` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M10`
- Phase: `Optimization`
- Priority: `P1`
- Issue count: `4`

## Scope

Add uncertainty and model-comparison APIs needed for scientific validation, publication-quality analysis, and autonomous model ranking.

## Mapped issues

- #80: Implement MCMC uncertainty API (`Optimization`, P0)
- #81: Implement optimizer result comparison utilities (`Optimization`, P0)
- #84: Implement model selection scoring interface (`Optimization`, P0)
- #85: Implement optimizer reproducibility seed management (`Optimization`, P0)

## Dependencies

- M08

## Required deliverables

- MCMC uncertainty API
- optimizer result comparison utilities
- model-selection scoring interface
- reproducibility seed management

## Acceptance criteria

- MCMC API can run a minimal synthetic posterior example or clearly skip when backend dependencies are absent.
- Model-comparison outputs record objective, parameter count, likelihood assumptions, and warnings.
- Seed handling is deterministic and documented.

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
