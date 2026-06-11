# Codex Prompt: M04 Residual objective and parameter transform foundation

## Objective

Implement the milestone `M04` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M04`
- Phase: `Physics and numerical engine`
- Priority: `P0`
- Issue count: `7`

## Scope

Implement the residual-vector interface, parameter scaling, bounded transforms, objective registry, robust losses, and Poisson likelihood path.

## Mapped issues

- #51: Implement residual vector interface (`Numerical Engine`, P0)
- #52: Implement parameter scaling utilities (`Numerical Engine`, P0)
- #53: Implement bounded parameter transforms (`Numerical Engine`, P0)
- #63: Implement safe invalid-model handling (`Numerical Engine`, P0)
- #64: Implement objective function registry (`Numerical Engine`, P0)
- #65: Implement robust loss functions (`Numerical Engine`, P0)
- #66: Implement Poisson likelihood objective (`Numerical Engine`, P0)

## Dependencies

- M02

## Required deliverables

- residual vector API
- parameter scaling utilities
- bounded transforms
- objective registry
- robust loss functions
- Poisson likelihood objective

## Acceptance criteria

- Gaussian least-squares, robust, and Poisson objectives are selectable through a common interface.
- Invalid parameter values are handled through transforms or structured errors.
- Small synthetic objective tests verify residual shapes and values.

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
