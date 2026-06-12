# M34 Completion Report

M34 covers validation and testing baseline issues #248-267. Implementation
source lives under `src/rietveld_next/validation/`; schemas live under
`schemas/`; documentation lives under `docs/`.

## Issue Closure Map

| Issue | Evidence |
| --- | --- |
| #248 Unit test conventions | `docs/unit_test_conventions.md` and package-local validation tests define deterministic test expectations. |
| #249 Golden dataset format | `schemas/golden_dataset.schema.json` and `GoldenDataset` define the fixture record. |
| #250 Synthetic dataset generator tests | `create_synthetic_profile_dataset()` is tested for determinism and invalid inputs. |
| #251 Scientific validation report template | `ValidationReport` and `schemas/validation_report.schema.json` define pass/fail summaries and known limitations. |
| #252 GSAS-II comparison test harness | `gsasii_comparison_harness()` supports explicit offline and configured dry-run modes. |
| #253 FullProf comparison placeholder | `ComparisonHarness` records explicit placeholder reasons for unavailable FullProf fixtures. |
| #254 TOPAS comparison placeholder | `ComparisonHarness` records explicit placeholder reasons for unavailable TOPAS fixtures. |
| #255 Numerical tolerance policy | `TolerancePolicy` requires absolute/relative tolerances, units, and rationale. |
| #256 Performance regression test harness | `compare_performance_regression()` and `PerformanceRegressionThreshold` provide an opt-in timing comparator. |
| #257 Cross-platform CI matrix | `validation_ci_matrix()` records default OS/Python targets. |
| #258 Package import smoke tests | `package_import_smoke_test()` imports packages deterministically. |
| #259 Source layout guard test | Existing architecture boundary tests remain part of the default validation command. |
| #260 Schema compatibility tests | Core schema tests plus new validation schemas parse in normal validation. |
| #261 Project round-trip tests | Existing project schema round-trip tests are included in the documented command. |
| #262 Benchmark result schema tests | Existing benchmark result schema tests remain part of package-local tests. |
| #263 UX visual regression setup | `VisualRegressionSnapshot` defines framework-neutral visual baseline metadata without screenshot files in default CI. |
| #264 AI behavior regression tests | Existing AI package tests and the validation baseline document deterministic AI behavior expectations. |
| #265 Security scanning workflow | `SecurityScanPolicy` provides local dependency-free secret-pattern checks. |
| #266 Documentation link checker | `check_markdown_links()` provides local Markdown link checks. |
| #267 Release validation checklist | `standard_release_checklist()` and `ReleaseChecklist` define required release gates. |

## Validation Commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next/validation
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next -p 'test*.py'
python3 -m json.tool schemas/golden_dataset.schema.json
python3 -m json.tool schemas/validation_report.schema.json
```

## Limitations

Cross-software GSAS-II, FullProf, and TOPAS comparisons are placeholders until
redistributable reference fixtures and backend invocation policies are approved.
Performance regression thresholds are documented as opt-in and do not run in
normal CI.
