# Release Process Guide

## Purpose

This guide defines the release checklist for early Rietveld Next milestones.

## Scope

Release candidates should include committed code, docs, schemas, validation
notes, and reproducible commands.

## Non-Goals

This process does not publish packages or automate PyPI/conda releases yet.

## Checklist

- Verify source layout guardrails.
- Run package-local unit tests.
- Parse JSON schemas.
- Confirm validation reports list limitations.
- Confirm docs link checks pass for local links.
- Review release artifact manifests.
- Confirm issue closure evidence maps to commits.

## Related Files

- [validation_baseline.md](validation_baseline.md)
- [m34_completion_report.md](m34_completion_report.md)
- [contributing.md](contributing.md)
