# Batch E Foundation

Batch E establishes framework-neutral foundations for workflows, deterministic
AI tool mediation, scheduler abstraction, UI command view models, and
visualization data transforms.

Completion evidence for the closed Batch E backlog issues is recorded in
[batch_e_completion_report.md](batch_e_completion_report.md).

## Scope

- Workflow replay lives in `src/rietveld_next/workflows/` and records ordered
  `WorkflowAction` entries for provenance.
- Sequential workflow helpers cover deterministic point execution, retry
  policy, previous-point initialization, parameter evolution export, batch
  recipes, checkpoints, comparison reports, and high-throughput summaries.
- AI tool contracts live in `src/rietveld_next/ai/` and fail closed when a tool,
  input field, or output field is missing.
- AI wrappers and diagnostics remain deterministic and tool-grounded, including
  safety checks, approval checkpoints, copilot report payloads, and evaluation
  scaffolding without LLM calls.
- Local scheduler primitives live in `src/rietveld_next/hpc/` and provide a
  deterministic in-process scheduler for tests and local batch execution.
- HPC/cloud helpers include dry-run scheduler payloads, optional adapter skip
  records, local result collection, status streams, retry/backoff, cancellation,
  and provenance capture without live cluster access.
- UI shell view models live in `src/rietveld_next/desktop/` and convert user
  commands into replayable workflow steps.
- UX view models cover project import, CIF validation, pattern views, parameter
  editing, diagnostics, reports, provenance timelines, command palettes, guided
  workflows, and expert mode without a UI framework dependency.
- Visualization transforms live in `src/rietveld_next/visualization/` and build
  display-only profile and difference series.
- Visualization payloads cover profile, multi-bank, residual heatmap,
  evolution, covariance/correlation, dependency graph, reflection browser,
  mask/exclusion, and publication-export request data.

## Boundaries

These APIs do not call LLMs, live schedulers, storage backends, or UI
frameworks. Scientific calculations remain in numerical packages, while
visualization only reshapes provided numeric arrays for display.

Cluster-specific integrations are represented as deterministic payloads and
skip-safe adapter records. Real cluster submission remains future work.

## Example

```python
from rietveld_next.desktop import ViewCommand, command_to_workflow_step
from rietveld_next.workflows import replay_workflow

command = ViewCommand("import_dataset", {"project_id": "p1", "path": "scan.xy"})
step = command_to_workflow_step(command, step_id="ui-1")
result = replay_workflow([step], {"import_dataset": lambda payload: {"accepted": True}})

assert result.succeeded
```
