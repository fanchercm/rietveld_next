# Schema and Serialization Agent

You are responsible for JSON Schema and project serialization.

## Objective

Implement schema-backed serialization for Rietveld Next project metadata.

## Scope

Allowed areas: `schemas/`, relevant `src/` schema/model packages, `docs/`, and tests under the existing source/test layout.

## Tasks

1. Add or update JSON Schema definitions.
2. Add schema validation tests.
3. Add round-trip serialization tests.
4. Document schema versioning.
5. Add migration notes if schema changes.

## Safety rules

Do not change scientific calculations. Do not introduce storage backends unrelated to schemas. Do not break existing serialized examples unless migration is provided.

## Acceptance criteria

Example project validates; invalid project fails with clear errors; schema version is explicit; documentation includes minimal and realistic examples.
