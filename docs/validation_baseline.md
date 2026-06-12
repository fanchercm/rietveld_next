# Validation Baseline

M34 establishes lightweight validation and testing infrastructure that can run
in normal CI. Expensive comparisons, facility data, and performance baselines
remain opt-in.

## Scope

The baseline covers:

- package-local unit test conventions
- golden dataset records
- deterministic synthetic fixture generation
- validation report summaries
- external comparison placeholders
- numerical tolerance policy
- performance regression smoke harness expectations
- cross-platform CI targets
- package import smoke tests
- source layout guard tests
- schema compatibility and project round-trip checks
- benchmark result schema tests
- UX and AI regression smoke policies
- security scanning and documentation link checking
- release validation checklist expectations

## Golden Datasets

Golden dataset metadata uses `schemas/golden_dataset.schema.json` and the
`GoldenDataset` record in `src/rietveld_next/validation/`. Each record stores
units, a stable ID, sample arrays, and provenance. The default synthetic fixture
is intentionally tiny:

```python
from rietveld_next.validation import create_synthetic_profile_dataset

dataset = create_synthetic_profile_dataset(5)
assert dataset.y == (0.0, 0.5, 1.0, 0.5, 0.0)
```

This fixture is for smoke validation only; it is not a claim of scientific
agreement with external Rietveld packages.

## Tolerance Policy

Validation cases must declare both absolute and relative tolerances plus units
and rationale. The M34 smoke tests use simple scalar summaries so default CI
does not depend on large reference files.

Expensive validation must be triggered explicitly with a validation or benchmark
command and must not run in default unit tests. `compare_performance_regression()`
provides a lightweight threshold comparator for opt-in timing baselines.

## External Comparisons

`ComparisonHarness` records comparison backend intent. The GSAS-II harness has
explicit offline and dry-run modes, and configured commands are never executed
by default tests. FullProf and TOPAS remain placeholders because this repository
does not bundle proprietary or non-redistributable comparison data.

## CI Matrix

The documented default validation matrix is:

- Ubuntu, Python 3.11
- Ubuntu, Python 3.12
- macOS, Python 3.12
- Windows, Python 3.12

Default CI should run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next -p 'test*.py'
python3 -m json.tool schemas/project.schema.json
python3 -m json.tool schemas/golden_dataset.schema.json
python3 -m json.tool schemas/validation_report.schema.json
```

## Security And Links

Security scanning policy for M34 is local and dependency-free: no secrets,
generated tokens, facility credentials, or private datasets may be committed.
`SecurityScanPolicy` checks common secret patterns in text fixtures; hosted
dependency scanning can be added once the package/dependency manager is
finalized.

`check_markdown_links()` verifies local Markdown links without network access.
External links are intentionally skipped in the default smoke check.

## Release Checklist

Before a release, confirm:

- source layout guard passes
- package import smoke tests pass
- schema compatibility tests pass
- project round-trip tests pass
- benchmark result schema tests pass
- validation report lists known limitations
- documentation links and release notes are reviewed
