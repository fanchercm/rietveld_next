# Codex Prompt: M36 Benchmarking foundation and result infrastructure

## Objective

Implement the milestone `M36` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M36`
- Phase: `Benchmarking`
- Priority: `P1`
- Issue count: `8`

## Scope

Define benchmark taxonomy, result schemas, backend comparison harnesses, and initial profile benchmark workflow.

## Mapped issues

- #288: Define benchmark taxonomy and naming convention (`Benchmarking`, P0)
- #289: Create benchmark result schema (`Benchmarking`, P0)
- #290: Create benchmark runner CLI skeleton (`Benchmarking`, P0)
- #291: Add deterministic synthetic profile dataset generator (`Benchmarking`, P0)
- #292: Implement Rust Gaussian profile microbenchmark (`Benchmarking`, P0)
- #293: Implement JAX Gaussian profile microbenchmark (`Benchmarking`, P0)
- #294: Compare Rust and JAX Gaussian profile outputs (`Benchmarking`, P0)
- #295: Add Markdown benchmark report generation (`Benchmarking`, P1)

## Dependencies

- M07

## Required deliverables

- benchmark taxonomy
- JSON result schema
- Rust/JAX benchmark harness
- profile benchmark docs

## Acceptance criteria

- Benchmarks write machine-readable results.
- Compile time and steady-state time are separated.
- Large benchmarks are opt-in.

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
