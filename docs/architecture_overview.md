# Architecture Overview

## Purpose

Rietveld Next separates metadata, numerical kernels, workflows, UI models, AI
tool boundaries, and HPC execution so scientific assumptions stay auditable.

## Scope

Implementation source lives under `src/rietveld_next/`. Persistent metadata is
defined by schemas under `schemas/`. Planning and prompt artifacts stay under
`backlog/` and `prompts/`.

## Non-Goals

This overview does not define scientific formulas or package every future
backend. Formula details belong in [numerical_kernels.md](numerical_kernels.md),
and source layout rules belong in [PACKAGE_TREE.md](PACKAGE_TREE.md).

## Layers

- `core`: architecture guardrails, project metadata, schema validation.
- `diffraction`, `xray`, `neutron`, `tof`, `edxrd`: physics-oriented helpers.
- `optimization`: residuals, objectives, transforms, diagnostics, optimizers.
- `storage`: project package and provenance IO.
- `workflows`: replayable recipes and sequential orchestration.
- `ai`: deterministic tool contracts and safety checks.
- `hpc`: local and cluster execution abstractions.
- `desktop` and `visualization`: framework-neutral view and plot payloads.
- `benchmarks` and `validation`: opt-in measurements and validation records.

## Example

A project JSON payload is validated by `core.schema`, converted to typed
`core.model` entities, passed to numerical or workflow helpers, and summarized
through validation or benchmark records. UI and AI layers should call typed
helpers instead of reimplementing model or numerical behavior.

## Related Files

- [PACKAGE_TREE.md](PACKAGE_TREE.md)
- [core_data_model.md](core_data_model.md)
- [schema_serialization.md](schema_serialization.md)
- [validation_baseline.md](validation_baseline.md)
