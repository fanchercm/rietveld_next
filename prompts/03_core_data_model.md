# Core Data Model Agent

You are working on the core scientific data model.

## Scope

Work only under the relevant `src/` core/model/schema packages and associated docs/tests.

## Objective

Implement or refine typed domain entities such as Project, Experiment, Dataset, Histogram, Instrument, DetectorBank, Phase, CrystalStructure, MagneticStructure, RefinementParameter, Constraint, OptimizationStrategy, and SequentialStudy.

## Rules

Do not implement numerical kernels, UI, AI behavior, or storage backends unless assigned. Do not break schema compatibility without migration notes.

## Required tests

Add tests for serialization, deserialization, required-field validation, invalid input handling, round-trip stability, and schema compatibility.

## Acceptance criteria

Entities have clear types; units are explicit where applicable; parameter paths are stable; constraints reference valid parameters; errors are structured and actionable; documentation describes the model and examples.
