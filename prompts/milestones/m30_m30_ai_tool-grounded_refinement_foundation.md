# Codex Prompt: M30 AI tool-grounded refinement foundation

## Objective

Implement the milestone `M30` as a coherent, reviewable increment for the Rietveld Next platform.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone metadata

- Milestone: `M30`
- Phase: `AI`
- Priority: `P1`
- Issue count: `20`

## Scope

Implement deterministic tool contracts, agent diagnostics, rollback-aware planning, and AI evaluation scaffolding.

## Mapped issues

- #183: Define AI tool contract schema (`AI and Agents`, P2)
- #184: Implement run_refinement tool wrapper (`AI and Agents`, P2)
- #185: Implement diagnose_residuals tool wrapper (`AI and Agents`, P2)
- #186: Implement set_refinement_flags tool wrapper (`AI and Agents`, P2)
- #187: Implement rollback tool wrapper (`AI and Agents`, P2)
- #188: Implement freeze_parameter tool wrapper (`AI and Agents`, P2)
- #189: Implement add_constraint tool wrapper (`AI and Agents`, P2)
- #190: Implement compare_models tool wrapper (`AI and Agents`, P2)
- #191: Implement strategy rule engine v0 (`AI and Agents`, P2)
- #192: Implement nonphysical solution detector (`AI and Agents`, P2)
- #193: Implement overfitting detector (`AI and Agents`, P2)
- #194: Implement residual pattern classifier skeleton (`AI and Agents`, P2)
- #195: Implement agent action log viewer (`AI and Agents`, P2)
- #196: Implement scientific copilot report generator (`AI and Agents`, P2)
- #197: Implement AI safety policy checks (`AI and Agents`, P2)
- #198: Implement AI evaluation benchmark suite (`AI and Agents`, P2)
- #199: Implement prompt injection regression tests (`AI and Agents`, P2)
- #200: Implement human approval checkpoint mechanism (`AI and Agents`, P2)
- #201: Implement knowledge-base citation model (`AI and Agents`, P2)
- #202: Implement autonomous recipe planner v0 (`AI and Agents`, P2)

## Dependencies

- M08
- M11
- M29

## Required deliverables

- AI tool schemas
- diagnostic tools
- agent action logs
- strategy rules
- AI evaluation tasks

## Acceptance criteria

- Every AI action maps to a deterministic tool call.
- Agent logs are replayable without the LLM.
- Safety tests cover nonphysical and overfitting scenarios.

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
