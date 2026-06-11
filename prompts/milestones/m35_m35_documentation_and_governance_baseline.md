# Codex Prompt: M35 Documentation and governance baseline

## Objective

Implement the milestone `M35` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M35`
- Phase: `Governance`
- Priority: `P1`
- Issue count: `20`

## Scope

Create user, developer, theory, governance, citation, and reproducibility documentation.

## Mapped issues

- #268: Write architecture overview (`Documentation and Governance`, P1)
- #269: Write src layout developer guide (`Documentation and Governance`, P1)
- #270: Write data model guide (`Documentation and Governance`, P1)
- #271: Write numerical engine theory guide (`Documentation and Governance`, P1)
- #272: Write optimization guide (`Documentation and Governance`, P1)
- #273: Write TOF refinement guide (`Documentation and Governance`, P1)
- #274: Write neutron refinement guide (`Documentation and Governance`, P1)
- #275: Write magnetic refinement guide (`Documentation and Governance`, P1)
- #276: Write EDXRD guide (`Documentation and Governance`, P1)
- #277: Write AI refinement guide (`Documentation and Governance`, P1)
- #278: Write HPC deployment guide (`Documentation and Governance`, P1)
- #279: Write plugin developer guide (`Documentation and Governance`, P1)
- #280: Write benchmark guide (`Documentation and Governance`, P1)
- #281: Write validation guide (`Documentation and Governance`, P1)
- #282: Write contribution guide (`Documentation and Governance`, P1)
- #283: Write code of conduct (`Documentation and Governance`, P1)
- #284: Write governance charter (`Documentation and Governance`, P1)
- #285: Write license and citation guide (`Documentation and Governance`, P1)
- #286: Write release process guide (`Documentation and Governance`, P1)
- #287: Write roadmap document (`Documentation and Governance`, P1)

## Dependencies

- M01
- M34

## Required deliverables

- theory guide
- beginner tutorial
- developer guide
- plugin guide
- governance docs
- citation guide

## Acceptance criteria

- Docs build successfully.
- Tutorials reference tested examples.
- Governance and contribution policies are explicit.

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
