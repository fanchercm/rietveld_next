# Codex Prompt: M34 Validation and testing baseline

## Objective

Implement the milestone `M34` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M34`
- Phase: `Quality`
- Priority: `P0`
- Issue count: `20`

## Scope

Establish scientific validation, golden regression tests, CI gates, and numerical tolerance policies.

## Mapped issues

- #248: Create unit test conventions (`Testing and Validation`, P0)
- #249: Create golden dataset format (`Testing and Validation`, P0)
- #250: Create synthetic dataset generator tests (`Testing and Validation`, P0)
- #251: Create scientific validation report template (`Testing and Validation`, P0)
- #252: Add GSAS-II comparison test harness (`Testing and Validation`, P0)
- #253: Add FullProf comparison placeholder (`Testing and Validation`, P0)
- #254: Add TOPAS comparison placeholder (`Testing and Validation`, P0)
- #255: Add numerical tolerance policy (`Testing and Validation`, P0)
- #256: Add performance regression test harness (`Testing and Validation`, P0)
- #257: Add cross-platform CI matrix (`Testing and Validation`, P0)
- #258: Add package import smoke tests (`Testing and Validation`, P0)
- #259: Add source layout guard test (`Testing and Validation`, P0)
- #260: Add schema compatibility tests (`Testing and Validation`, P0)
- #261: Add project round-trip tests (`Testing and Validation`, P0)
- #262: Add benchmark result schema tests (`Testing and Validation`, P0)
- #263: Add UX visual regression setup (`Testing and Validation`, P0)
- #264: Add AI behavior regression tests (`Testing and Validation`, P0)
- #265: Add security scanning workflow (`Testing and Validation`, P0)
- #266: Add documentation link checker (`Testing and Validation`, P0)
- #267: Add release validation checklist (`Testing and Validation`, P0)

## Dependencies

- M03
- M15
- M19
- M22

## Required deliverables

- unit/integration tests
- golden scientific cases
- optimizer regression suite
- cross-platform CI
- validation report generator

## Acceptance criteria

- Validation tests run in CI with documented tolerances.
- Expensive tests are clearly marked.
- Validation report summarizes pass/fail and known limitations.

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
