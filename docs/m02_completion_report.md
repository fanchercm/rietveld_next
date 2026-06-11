# M02 Completion Report

M02 covers the core project model and schema milestone for issues #16-35. The
implementation source lives under `src/rietveld_next/core/model/` and
`src/rietveld_next/core/schema/`, with the persistent JSON Schema in
`schemas/project.schema.json`.

## Issue Closure Map

| Issue | Evidence |
| --- | --- |
| #16 Project | `Project` validates schema version, IDs, uniqueness, references, deterministic JSON, and graph diffs. |
| #17 Experiment | `Experiment` models radiation, datasets, instrument references, and sample-environment metadata. |
| #18 Dataset | `Dataset` models axis, data URI, uncertainty model, histograms, and metadata. |
| #19 Histogram | `Histogram` models dataset, detector-bank, array, background, and phase references. |
| #20 Instrument | `Instrument` models radiation metadata and detector-bank collections. |
| #21 DetectorBank | `DetectorBank` models bank identity, axis, calibration metadata, and masks. |
| #22 Phase | `Phase` models material identity, crystal structure, optional magnetic structure, microstructure, and texture metadata. |
| #23 CrystalStructure | `CrystalStructure` validates finite unit-cell metadata and preserves atom-site records. |
| #24 MagneticStructure | `MagneticStructure` validates three-component propagation vectors, with focused success and failure tests. |
| #25 RefinementParameter | `RefinementParameter` models stable paths, values, refine flags, units, uncertainty, bounds, priors, owners, and metadata. |
| #26 Constraint | `Constraint` models parameter references and `Project` rejects unknown referenced parameters. |
| #27 OptimizationStrategy | `OptimizationStrategy` models reproducible method metadata and validates parameter references. |
| #28 SequentialStudy | `SequentialStudy` and `SequentialPoint` model shared parameters and dataset-indexed sequential points. |
| #29 Parameter path addressing | `ParameterPath` parses and emits stable slash-delimited owner/value addresses. |
| #30 Typed units metadata | `UnitMetadata` is preserved under `unit`; legacy `units` strings are accepted on input. |
| #31 Bounds and priors metadata | `Bounds` and `Prior` validate finite ordered metadata and round-trip through schema-backed JSON. |
| #32 Entity ID validation | Shared entity ID validation is enforced by typed model constructors and JSON Schema patterns. |
| #33 Model graph serialization | `Project.to_json()`, `Project.from_json()`, `project_to_json()`, and `project_from_json()` provide deterministic schema-backed serialization. |
| #34 Model graph diffing | `Project.diff()` reports changed stable IDs across graph collections plus project/provenance changes. |
| #35 Model graph migration harness | `plan_project_migration()` and `migrate_project_mapping()` support deterministic `1.0.x` patch-line normalization and reject unsupported schema lines. |

## Validation

Reproduce M02 validation with:

```bash
PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next/core
python3 -m json.tool schemas/project.schema.json
```

No expensive benchmarks, GPU jobs, or facility-only validation data are required
for this milestone.

## Layout Confirmation

All implementation code for M02 remains under `src/`. Tests are package-local
under `src/rietveld_next/core/**/tests/`. Documentation remains under `docs/`,
and the project schema remains under `schemas/`.
