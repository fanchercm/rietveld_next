# Core Data Model

This document describes the first typed Python domain entities for the Rietveld
Next core model. The implementation lives under
`src/rietveld_next/core/model/` and intentionally covers metadata and graph
validation only. It does not implement numerical kernels, storage backends, UI,
or AI behavior. Key durable facts are recorded in
[ground_truths.md](ground_truths.md). Schema-backed serialization is documented
in [schema_serialization.md](schema_serialization.md).

## Entities

The package defines these core entities:

- `Project`
- `Experiment`
- `Dataset`
- `Histogram`
- `Instrument`
- `DetectorBank`
- `Phase`
- `CrystalStructure`
- `MagneticStructure`
- `RefinementParameter`
- `Constraint`
- `OptimizationStrategy`
- `SequentialStudy`

Each entity uses typed dataclasses with package-local validation. Public
validation failures raise `ModelValidationError`, which includes a stable error
code, message, optional model path, and structured details.

## Parameter Paths

Refinement parameters use stable slash-delimited paths:

```text
phase/phase1/crystal_structure/cell/a
```

The first segment is the owner type, the second segment is the owner ID, and the
remaining segments address the owned value. Path segments must start with a
letter and may contain letters, digits, `_`, `.`, `:`, or `-`.

## Units, Bounds, And Priors

Numeric refinement parameters may carry:

- `UnitMetadata`: explicit unit symbol, quantity, and optional SI conversion
  factor.
- `Bounds`: inclusive lower and upper bounds.
- `Prior`: distribution name and numeric parameters.

The model validates finite numeric values, ordered bounds, non-negative standard
uncertainties, and values that fall inside declared bounds.
The schema-compatible representation preserves full `UnitMetadata` under the
`unit` field. Legacy input payloads that use a `units` string are still accepted
and converted to `UnitMetadata` with `quantity="unspecified"`.

## Constraints And References

Constraints reference refinement parameters by ID. A `Project` validates that:

- Entity IDs are unique within each collection.
- Constraint parameter IDs exist.
- Optimization strategy parameter IDs exist.
- Sequential study parameter and dataset references exist.
- Histogram phase references exist.
- Instrument and detector-bank references exist when instruments are supplied.

## Serialization

`Project.to_json()` emits deterministic JSON with sorted object keys and the
schema-compatible fields required by `schemas/project.schema.json`.
`Project.from_json()` performs structured deserialization and validation.
`Project.diff()` compares stable entity IDs across instruments, experiments,
phases, parameters, constraints, strategies, and sequential studies, and reports
top-level project or provenance changes separately.

Example:

```python
from rietveld_next.core.model import (
    Bounds,
    CrystalStructure,
    ParameterPath,
    Phase,
    Project,
    RefinementParameter,
    UnitMetadata,
)

phase = Phase(
    id="phase1",
    name="Silicon",
    crystal_structure=CrystalStructure(space_group="Fd-3m", cell={"a": 5.431}),
)
parameter = RefinementParameter(
    id="p_cell_a",
    path=ParameterPath("phase", "phase1", ("crystal_structure", "cell", "a")),
    value=5.431,
    refine=True,
    unit=UnitMetadata(symbol="angstrom", quantity="length", scale_to_si=1.0e-10),
    bounds=Bounds(lower=5.0, upper=6.0),
)
project = Project(
    id="project1",
    experiments=[],
    phases=[phase],
    parameters=[parameter],
)

payload = project.to_json()
loaded = Project.from_json(payload)
assert loaded.to_json() == payload
```

## Migration Harness

Project metadata migration helpers live in `src/rietveld_next/core/schema/`.
M02 supports the `1.0.x` compatibility line. `plan_project_migration()` returns
an explicit no-change plan for already-current payloads or a deterministic
patch-line normalization step. Unsupported major or minor versions raise
`ModelValidationError` with code `unsupported_schema_version`.

## Current Limitations

- The model layer does not claim scientific correctness for calculations; it
  only validates metadata shape, units, IDs, and references.
- `schemas/project.schema.json` remains on the `1.0.x` compatibility line and
  intentionally keeps legacy `units` input compatibility while emitting full
  `unit` metadata from the typed model.
- Cross-software validation data is not included in this metadata-only
  increment.
- Build-system conventions are not changed here because M01 workspace
  conventions remain a separate architecture workstream.

## Validation Command

Run the package-local tests with:

```bash
PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next/core/model/tests
```

Run the full core foundation test set, including source-layout guard checks,
with:

```bash
PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next/core
```
