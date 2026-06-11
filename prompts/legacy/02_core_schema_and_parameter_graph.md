# Codex Prompt: Core Schema and Parameter Graph

Implement the first usable domain model and parameter graph.

Inputs:

- `schemas/project.schema.json`
- `sections/04_scientific_data_model.md`
- `inputs/repository_boundaries.md`

Deliverables:

- Rust structs for Project, Experiment, Dataset, Histogram, Instrument, DetectorBank, Phase, Parameter, Constraint, and ProvenanceEvent.
- Serde serialization/deserialization.
- JSON Schema validation test fixtures.
- Parameter graph that tracks dependencies and constraint expressions.
- Python bindings or placeholder API matching the Rust model.

Acceptance criteria:

- Round-trip JSON serialization works.
- Invalid schemas fail with useful errors.
- Constraint dependencies can be queried.
- Unit tests cover bounds, refine flags, parameter paths, and provenance events.
