# Codex Prompt: M38 Physics workflow benchmark suite

## Objective

Implement the milestone `M38` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M38`
- Phase: `Benchmarking`
- Priority: `P1`
- Issue count: `8`

## Scope

Benchmark sequential, parametric, batch, TOF, neutron, magnetic, and EDXRD workflows.

## Mapped issues

- #304: Benchmark global multi-start refinement workflow (`Benchmarking`, P2)
- #305: Implement sequential refinement benchmark (`Benchmarking`, P1)
- #306: Implement parametric refinement benchmark (`Benchmarking`, P2)
- #307: Implement batch throughput benchmark (`Benchmarking`, P1)
- #308: Implement multi-bank TOF profile benchmark (`Benchmarking`, P1)
- #309: Benchmark TOF calibration refinement (`Benchmarking`, P2)
- #310: Implement neutron scattering factor table lookup benchmark (`Benchmarking`, P2)
- #311: Implement magnetic structure-factor proxy benchmark (`Benchmarking`, P2)

## Dependencies

- M21
- M25
- M28
- M29

## Required deliverables

- sequential benchmark
- parametric benchmark
- TOF benchmark
- magnetic benchmark
- EDXRD benchmark

## Acceptance criteria

- Each benchmark documents scientific assumptions.
- Workflow benchmarks produce result tables and diagnostics.
- Benchmarks are usable for regression tracking.

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
