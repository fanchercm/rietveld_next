# Codex Prompt: M39 Storage, diagnostics, visualization, AI, and HPC benchmark suite

## Objective

Implement the milestone `M39` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M39`
- Phase: `Benchmarking`
- Priority: `P2`
- Issue count: `9`

## Scope

Benchmark storage backends, visualization payloads, diagnostics, AI-agent loops, schedulers, and distributed execution.

## Mapped issues

- #312: Implement EDXRD detector-response benchmark (`Benchmarking`, P1)
- #313: Benchmark EDXRD calibration workflow (`Benchmarking`, P2)
- #314: Benchmark storage write/read for project packages (`Benchmarking`, P1)
- #315: Benchmark Zarr profile-array IO (`Benchmarking`, P2)
- #316: Benchmark Parquet result-table IO (`Benchmarking`, P2)
- #317: Benchmark visualization data decimation (`Benchmarking`, P2)
- #318: Benchmark residual diagnostic computation (`Benchmarking`, P1)
- #319: Benchmark covariance and correlation computation (`Benchmarking`, P1)
- #320: Benchmark AI tool-call overhead (`Benchmarking`, P2)

## Dependencies

- M30
- M32
- M33

## Required deliverables

- storage benchmark
- diagnostics benchmark
- visualization benchmark
- AI loop benchmark
- scheduler benchmark

## Acceptance criteria

- Benchmarks produce comparable JSON artifacts.
- Scheduler benchmarks can run locally with fake adapters.
- AI benchmarks do not depend on nondeterministic LLM output for pass/fail.

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
