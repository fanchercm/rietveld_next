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

## Current Limitations

- The model layer does not claim scientific correctness for calculations; it
  only validates metadata shape, units, IDs, and references.
- `schemas/project.schema.json` is currently permissive and remains on the
  `1.0.x` compatibility line.
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
