# Batch E Foundation

Batch E establishes framework-neutral foundations for workflows, deterministic
AI tool mediation, scheduler abstraction, UI command view models, and
visualization data transforms.

## Scope

- Workflow replay lives in `src/rietveld_next/workflows/` and records ordered
  `WorkflowAction` entries for provenance.
- AI tool contracts live in `src/rietveld_next/ai/` and fail closed when a tool,
  input field, or output field is missing.
- Local scheduler primitives live in `src/rietveld_next/hpc/` and provide a
  deterministic in-process scheduler for tests and local batch execution.
- UI shell view models live in `src/rietveld_next/desktop/` and convert user
  commands into replayable workflow steps.
- Visualization transforms live in `src/rietveld_next/visualization/` and build
  display-only profile and difference series.

## Boundaries

These APIs do not call LLMs, live schedulers, storage backends, or UI
frameworks. Scientific calculations remain in numerical packages, while
visualization only reshapes provided numeric arrays for display.

The local scheduler is a testable abstraction, not a Slurm, Kubernetes, Dask, or
Ray adapter. Cluster-specific adapters should be added as optional integrations
with skip-safe tests.

## Example

```python
from rietveld_next.desktop import ViewCommand, command_to_workflow_step
from rietveld_next.workflows import replay_workflow

command = ViewCommand("import_dataset", {"project_id": "p1", "path": "scan.xy"})
step = command_to_workflow_step(command, step_id="ui-1")
result = replay_workflow([step], {"import_dataset": lambda payload: {"accepted": True}})

assert result.succeeded
```
