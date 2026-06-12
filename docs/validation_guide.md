# Validation Guide

## Purpose

This guide explains how validation evidence should be recorded.

## Scope

Validation reports should include cases, tolerances, pass/fail status,
provenance, and known limitations. Golden fixtures should use documented units
and deterministic generators.

## Non-Goals

Placeholder external comparisons must not be represented as scientific
agreement. Expensive validation remains opt-in.

## Example

Create a `ValidationCase` with expected and observed scalar summaries, attach a
`TolerancePolicy`, and include the case in a `ValidationReport` with explicit
known limitations.

## Related Files

- [validation_baseline.md](validation_baseline.md)
- [../validation/validation_plan.md](../validation/validation_plan.md)
