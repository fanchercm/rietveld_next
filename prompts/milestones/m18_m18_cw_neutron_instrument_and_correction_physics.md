# Codex Prompt: M18 CW neutron instrument and correction physics

## Objective

Implement the milestone `M18` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M18`
- Phase: `Physics calculation`
- Priority: `P1`
- Issue count: `5`

## Scope

Implement CW neutron instrument modeling, isotope scattering lookup, absorption hooks, sample geometry corrections, and extinction interfaces.

## Mapped issues

- #116: Implement CW neutron instrument model (`Neutron`, P1)
- #117: Implement isotope scattering-length lookup (`Neutron`, P1)
- #118: Implement wavelength-dependent absorption hooks (`Neutron`, P1)
- #119: Implement sample geometry correction interface (`Neutron`, P1)
- #120: Implement extinction correction interface (`Neutron`, P1)

## Dependencies

- M13
- M15

## Required deliverables

- CW neutron instrument model
- isotope scattering-length lookup
- wavelength-dependent absorption hooks
- sample geometry correction interface
- extinction correction interface

## Acceptance criteria

- Neutron instrument models use neutron scattering lengths rather than X-ray form factors.
- Absorption/extinction interfaces can be attached without changing core profile kernels.
- Reference neutron calculations pass baseline validation.

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
