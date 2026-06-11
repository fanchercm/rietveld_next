# Schema Serialization

Rietveld Next project metadata is serialized as deterministic JSON and
validated against `schemas/project.schema.json`. The schema-backed helpers live
under `src/rietveld_next/core/schema/`.

## Schema Version

The current project schema accepts the `1.0.x` compatibility line:

```json
{
  "schema_version": "1.0.0"
}
```

Patch versions in the `1.0.x` line may add optional metadata fields or tighten
validation for fields already enforced by the typed model. Breaking changes
must use a new schema version line and include migration notes.

## Minimal Example

```json
{
  "schema_version": "1.0.0",
  "id": "project1",
  "experiments": [],
  "phases": [],
  "parameters": []
}
```

## Realistic Example Shape

```json
{
  "schema_version": "1.0.0",
  "id": "project1",
  "name": "Schema serialization example",
  "instruments": [
    {
      "id": "inst1",
      "radiation": "lab_xray_cw",
      "detector_banks": [
        {
          "id": "bank1",
          "axis": "two_theta"
        }
      ]
    }
  ],
  "experiments": [
    {
      "id": "exp1",
      "radiation": "lab_xray_cw",
      "instrument_id": "inst1",
      "datasets": [
        {
          "id": "dataset1",
          "axis": "two_theta",
          "data_uri": "arrays/profile"
        }
      ]
    }
  ],
  "phases": [
    {
      "id": "phase1",
      "name": "Silicon",
      "crystal_structure": {
        "space_group": "Fd-3m",
        "cell": {
          "a": 5.431
        }
      }
    }
  ],
  "parameters": [
    {
      "id": "p_cell_a",
      "path": "phase/phase1/crystal_structure/cell/a",
      "value": 5.431,
      "refine": true,
      "unit": {
        "symbol": "angstrom",
        "quantity": "length",
        "scale_to_si": 1.0e-10
      },
      "bounds": [5.0, 6.0],
      "prior": {
        "distribution": "normal",
        "parameters": {
          "mean": 5.431,
          "sigma": 0.05
        }
      }
    }
  ]
}
```

## Python API

```python
from rietveld_next.core.schema import (
    migrate_project_mapping,
    plan_project_migration,
    project_from_json,
    project_to_json,
    validate_project_mapping,
)

payload = project_to_json(project)
loaded_project = project_from_json(payload)
validate_project_mapping(loaded_project.to_schema_dict())
plan = plan_project_migration("1.0.9")
migrated = migrate_project_mapping({"schema_version": "1.0.9", "id": "p", "experiments": [], "phases": [], "parameters": []})
```

`SchemaValidationError` reports deterministic issues with a JSON path, message,
and schema keyword. Model graph errors, such as constraints referencing missing
parameters, are reported by `ModelValidationError` after schema validation
succeeds.

The typed model emits full unit metadata under `unit`. The schema still accepts
legacy `units` strings for `1.0.x` payloads; deserialization converts them to
`UnitMetadata(symbol=<units>, quantity="unspecified")`.
Schema validation rejects empty unit symbols or quantities, non-positive SI
scales, empty prior distributions, and non-numeric prior parameter values before
model deserialization.

## Migration Harness

`plan_project_migration()` and `migrate_project_mapping()` provide the M02
schema migration harness. The current harness supports only the `1.0.x`
compatibility line. Patch-line payloads are deep-copied and normalized to the
target schema version, while unsupported major or minor lines fail with
`ModelValidationError` code `unsupported_schema_version`.

## Migration Notes

This increment is additive within `1.0.x`:

- `instruments`, `strategies`, and `studies` are now described by the schema.
- Entity IDs and parameter paths are validated with explicit patterns.
- Crystal and magnetic structure metadata have documented schema shapes.
- Full `unit` metadata and structured prior metadata are described by the
  schema, while legacy `units` strings remain valid input.

No existing valid minimal `1.0.x` project payload is intentionally broken.

## Validation Command

Run schema and model serialization tests with:

```bash
PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next/core
```

This command also runs the source-layout guard tests that enforce
`docs/PACKAGE_TREE.md` as the canonical package-tree location and reject
forbidden top-level implementation directories.
