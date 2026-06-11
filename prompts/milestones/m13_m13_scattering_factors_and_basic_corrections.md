# Codex Prompt: M13 Scattering factors and basic corrections

## Objective

Implement the milestone `M13` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M13`
- Phase: `Physics calculation`
- Priority: `P0`
- Issue count: `4`

## Scope

Implement scattering tables and first-pass diffraction corrections needed by X-ray and neutron calculations.

## Mapped issues

- #90: Implement X-ray form factor table (`Diffraction Models`, P1)
- #91: Implement neutron scattering length table (`Diffraction Models`, P1)
- #92: Implement multiplicity calculation (`Diffraction Models`, P1)
- #93: Implement Lorentz-polarization correction (`Diffraction Models`, P1)

## Dependencies

- M12

## Required deliverables

- X-ray form factor table
- neutron scattering length table
- multiplicity calculation
- Lorentz-polarization correction

## Acceptance criteria

- Scattering tables include citation/provenance metadata.
- Multiplicity and Lorentz-polarization tests match reference calculations.
- X-ray and neutron scattering lookup APIs are radiation-specific.

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
