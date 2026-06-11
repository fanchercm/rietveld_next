# Codex Prompt: M40 Benchmark regression, dashboard, and CI integration

## Objective

Implement the milestone `M40` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M40`
- Phase: `Benchmarking`
- Priority: `P1`
- Issue count: `7`

## Scope

Integrate benchmark baselines, dashboards, regression thresholds, CI smoke benchmarks, and documentation.

## Mapped issues

- #321: Benchmark agent replay and provenance validation (`Benchmarking`, P2)
- #322: Benchmark Slurm job-array packaging overhead (`Benchmarking`, P2)
- #323: Benchmark Ray or Dask local scheduler overhead (`Benchmarking`, P2)
- #324: Add benchmark regression baseline mechanism (`Benchmarking`, P1)
- #325: Add benchmark dashboard artifact generation (`Benchmarking`, P2)
- #326: Add benchmark documentation hub (`Benchmarking`, P1)
- #327: Create benchmark validation CI workflow (`Benchmarking`, P1)

## Dependencies

- M36
- M37
- M38
- M39

## Required deliverables

- benchmark baseline registry
- dashboard artifact
- performance regression thresholds
- CI smoke benchmark
- benchmark documentation

## Acceptance criteria

- CI runs lightweight benchmarks only.
- Regression thresholds are explicit and reviewable.
- Dashboard artifacts can be regenerated from JSON results.

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
