# M35 Completion Report

M35 covers documentation and governance baseline issues #268-287.

## Issue Closure Map

| Issue | Evidence |
| --- | --- |
| #268 Architecture overview | [architecture_overview.md](architecture_overview.md) |
| #269 Src layout developer guide | [PACKAGE_TREE.md](PACKAGE_TREE.md) and [contributing.md](contributing.md) |
| #270 Data model guide | [core_data_model.md](core_data_model.md) |
| #271 Numerical engine theory guide | [numerical_engine_theory.md](numerical_engine_theory.md) |
| #272 Optimization guide | [optimization.md](optimization.md) |
| #273 TOF refinement guide | [tof_refinement_guide.md](tof_refinement_guide.md) |
| #274 Neutron refinement guide | [neutron_refinement_guide.md](neutron_refinement_guide.md) |
| #275 Magnetic refinement guide | [magnetic_refinement_guide.md](magnetic_refinement_guide.md) |
| #276 EDXRD guide | [edxrd_guide.md](edxrd_guide.md) |
| #277 AI refinement guide | [ai_refinement_guide.md](ai_refinement_guide.md) |
| #278 HPC deployment guide | [hpc_deployment_guide.md](hpc_deployment_guide.md) |
| #279 Plugin developer guide | [plugin_developer_guide.md](plugin_developer_guide.md) |
| #280 Benchmark guide | [benchmark_guide.md](benchmark_guide.md) |
| #281 Validation guide | [validation_guide.md](validation_guide.md) |
| #282 Contribution guide | [contributing.md](contributing.md) |
| #283 Code of conduct | [code_of_conduct.md](code_of_conduct.md) |
| #284 Governance charter | [governance_charter.md](governance_charter.md) |
| #285 License and citation guide | [license_and_citation.md](license_and_citation.md) |
| #286 Release process guide | [release_process.md](release_process.md) |
| #287 Roadmap document | [roadmap.md](roadmap.md) |

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next/validation
```

The validation tests check that required M35 docs exist, include actionable
sections, and have valid local Markdown links.
