# Codex Prompt: M37 Numerical and optimization benchmark suite

## Objective

Implement the milestone `M37` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M37`
- Phase: `Benchmarking`
- Priority: `P1`
- Issue count: `8`

## Scope

Benchmark profile kernels, sparse Jacobians, AD, local optimizers, global optimizers, and uncertainty APIs.

## Mapped issues

- #296: Add benchmark environment metadata capture (`Benchmarking`, P1)
- #297: Add benchmark skip policy for optional dependencies (`Benchmarking`, P1)
- #298: Implement pseudo-Voigt profile microbenchmark (`Benchmarking`, P1)
- #299: Implement profile windowing benchmark (`Benchmarking`, P1)
- #300: Implement sparse Jacobian assembly benchmark (`Benchmarking`, P1)
- #301: Implement automatic differentiation benchmark (`Benchmarking`, P1)
- #302: Implement local optimizer benchmark harness (`Benchmarking`, P1)
- #303: Benchmark optimizer scaling with parameter count (`Benchmarking`, P2)

## Dependencies

- M08
- M09

## Required deliverables

- pseudo-Voigt benchmark
- Jacobian benchmark
- AD benchmark
- optimizer benchmark
- global search benchmark

## Acceptance criteria

- Benchmark outputs include size, backend, dtype, iterations, timings, and checksum.
- Baseline results are reproducible.
- Benchmark tests avoid expensive defaults.

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
