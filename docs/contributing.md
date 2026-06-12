# Contributing Guide

## Purpose

This guide defines contribution expectations for Rietveld Next.

## Scope

Contributions should be small, deterministic, tested, documented, and scoped to
one issue or milestone.

## Non-Goals

Do not perform broad rewrites, move large directory trees, or change scientific
behavior without tests and documentation.

## Workflow

1. Read `AGENTS.md`, [PACKAGE_TREE.md](PACKAGE_TREE.md), the relevant issue
   prompt, and related docs.
2. Keep implementation source under `src/`.
3. Add package-local tests under `src/rietveld_next/**/tests/`.
4. Document public APIs, formulas, workflows, and limitations.
5. Run lightweight validation commands before requesting review.

## Related Files

- [unit_test_conventions.md](unit_test_conventions.md)
- [validation_baseline.md](validation_baseline.md)
- [release_process.md](release_process.md)
