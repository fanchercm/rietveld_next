# Codex Prompt: Neutron Workstream

## Objective

Plan and implement a coherent sequence of issues in the **Neutron** workstream.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Issues in this workstream

- #116: Implement CW neutron instrument model (P1, phase: Neutron)
- #117: Implement isotope scattering-length lookup (P1, phase: Neutron)
- #118: Implement wavelength-dependent absorption hooks (P1, phase: Neutron)
- #119: Implement sample geometry correction interface (P1, phase: Neutron)
- #120: Implement extinction correction interface (P1, phase: Neutron)
- #121: Implement container background model (P1, phase: Neutron)
- #122: Implement neutron joint weighting model (P1, phase: Neutron)
- #123: Implement nuclear neutron validation example (P1, phase: Neutron)
- #124: Implement Mantid reduced-data import adapter (P1, phase: Neutron)
- #125: Implement neutron uncertainty model checks (P1, phase: Neutron)

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
