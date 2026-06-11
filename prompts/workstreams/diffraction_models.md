# Codex Prompt: Diffraction Models Workstream

## Objective

Plan and implement a coherent sequence of issues in the **Diffraction Models** workstream.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issues in this workstream

- #86: Implement CIF import v0 (P1, phase: Scientific Models)
- #87: Implement CIF validation report (P1, phase: Scientific Models)
- #88: Implement space-group lookup service (P1, phase: Scientific Models)
- #89: Implement reflection generation service (P1, phase: Scientific Models)
- #90: Implement X-ray form factor table (P1, phase: Scientific Models)
- #91: Implement neutron scattering length table (P1, phase: Scientific Models)
- #92: Implement multiplicity calculation (P1, phase: Scientific Models)
- #93: Implement Lorentz-polarization correction (P1, phase: Scientific Models)
- #94: Implement preferred orientation model v0 (P1, phase: Scientific Models)
- #95: Implement isotropic size broadening (P1, phase: Scientific Models)
- #96: Implement isotropic strain broadening (P1, phase: Scientific Models)
- #97: Implement background polynomial model (P1, phase: Scientific Models)
- #98: Implement Chebyshev background model (P1, phase: Scientific Models)
- #99: Implement reflection tick generation (P1, phase: Scientific Models)
- #100: Implement synthetic pattern generator (P1, phase: Scientific Models)
- #101: Implement standard reference dataset registry (P1, phase: Scientific Models)
- #102: Implement phase scale model (P1, phase: Scientific Models)
- #103: Implement phase fraction calculation (P1, phase: Scientific Models)
- #104: Implement atom occupancy constraints (P1, phase: Scientific Models)
- #105: Implement ADP validation checks (P1, phase: Scientific Models)

## Execution guidance

- Start with P0 issues and dependency-free issues.
- Prefer milestone prompts for multi-issue implementation.
- Prefer individual issue prompts for targeted pull requests.
- Keep scientific claims tied to tests, fixtures, or documentation.
- Avoid broad rewrites unless an issue explicitly requires an architecture change.

## Final response requested from Codex

Report:

- Issues completed.
- Issues partially completed.
- Tests and validation commands run.
- Follow-up issue recommendations.
