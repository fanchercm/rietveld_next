# Codex Prompt: M31 Desktop and web UX foundation

## Objective

Implement the milestone `M31` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M31`
- Phase: `UX`
- Priority: `P1`
- Issue count: `20`

## Scope

Build the first desktop/web user experience for import, visualization, parameter editing, guided workflows, and reports.

## Mapped issues

- #203: Implement desktop shell src layout (`UX Desktop and Web`, P1)
- #204: Implement project open screen (`UX Desktop and Web`, P1)
- #205: Implement data import screen (`UX Desktop and Web`, P1)
- #206: Implement CIF validation screen (`UX Desktop and Web`, P1)
- #207: Implement pattern viewer (`UX Desktop and Web`, P1)
- #208: Implement reflection tick overlay (`UX Desktop and Web`, P1)
- #209: Implement difference plot panel (`UX Desktop and Web`, P1)
- #210: Implement parameter table (`UX Desktop and Web`, P1)
- #211: Implement parameter graph view (`UX Desktop and Web`, P1)
- #212: Implement constraint editor (`UX Desktop and Web`, P1)
- #213: Implement correlation heatmap (`UX Desktop and Web`, P1)
- #214: Implement covariance detail view (`UX Desktop and Web`, P1)
- #215: Implement sequential dashboard (`UX Desktop and Web`, P1)
- #216: Implement residual diagnostics panel (`UX Desktop and Web`, P1)
- #217: Implement refinement recipe wizard (`UX Desktop and Web`, P1)
- #218: Implement beginner guided workflow (`UX Desktop and Web`, P1)
- #219: Implement expert mode toggle (`UX Desktop and Web`, P1)
- #220: Implement report export UI (`UX Desktop and Web`, P1)
- #221: Implement provenance timeline UI (`UX Desktop and Web`, P1)
- #222: Implement keyboard command palette (`UX Desktop and Web`, P1)

## Dependencies

- M01
- M02
- M08

## Required deliverables

- desktop shell
- web app skeleton
- pattern viewer
- parameter table
- guided workflow screens
- report export

## Acceptance criteria

- Core workflows are accessible from GUI and script API.
- GUI actions emit provenance events.
- UX tests cover import-through-simple-refinement path.

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
