# Codex Prompts

This directory contains the expanded prompt set aligned to the canonical backlog.

## Counts

- Program prompts: 1
- Milestone prompts: 40
- Individual issue prompts: 327
- Workstream prompts: 19
- Legacy prompts retained under `prompts/legacy/`

## Recommended usage

- Use `program/00_program_execution_brief.md` for full-context bootstrapping.
- Use `milestones/Mxx_*.md` for coherent milestone-sized implementation.
- Use `issues/issue_NNN_*.md` for focused pull requests.
- Use `workstreams/*.md` for planning or sequencing by domain.

## Repository guardrail

All implementation source code must live under `src/`. Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, `web/`, `benchmarks/`, or `tests/`. Documentation may live under `docs/`, backlog files under `backlog/`, GitHub import payloads under `github/`, schemas under `schemas/`, prompts under `prompts/`, and scaffold notes under `scaffold/`.

## Milestone prompts

- [M01 — M01 Src-first architecture foundation](milestones/m01_m01_src-first_architecture_foundation.md)
- [M02 — M02 Core project model and schemas](milestones/m02_m02_core_project_model_and_schemas.md)
- [M03 — M03 Storage and data interchange foundation](milestones/m03_m03_storage_and_data_interchange_foundation.md)
- [M04 — M04 Residual objective and parameter transform foundation](milestones/m04_m04_residual_objective_and_parameter_transform_foundation.md)
- [M05 — M05 Derivative and sparse Jacobian infrastructure](milestones/m05_m05_derivative_and_sparse_jacobian_infrastructure.md)
- [M06 — M06 Profile kernel and reflection batching foundation](milestones/m06_m06_profile_kernel_and_reflection_batching_foundation.md)
- [M07 — M07 Uncertainty diagnostics and profile benchmark harness](milestones/m07_m07_uncertainty_diagnostics_and_profile_benchmark_harness.md)
- [M08 — M08 Local optimization adapters and rollback state](milestones/m08_m08_local_optimization_adapters_and_rollback_state.md)
- [M09 — M09 Global and multi-start optimization foundation](milestones/m09_m09_global_and_multi-start_optimization_foundation.md)
- [M10 — M10 Probabilistic uncertainty and model comparison foundation](milestones/m10_m10_probabilistic_uncertainty_and_model_comparison_foundation.md)
- [M11 — M11 Optimizer safeguard heuristics](milestones/m11_m11_optimizer_safeguard_heuristics.md)
- [M12 — M12 Structural IO and symmetry baseline](milestones/m12_m12_structural_io_and_symmetry_baseline.md)
- [M13 — M13 Scattering factors and basic corrections](milestones/m13_m13_scattering_factors_and_basic_corrections.md)
- [M14 — M14 Orientation, microstructure, and background models](milestones/m14_m14_orientation,_microstructure,_and_background_models.md)
- [M15 — M15 Synthetic patterns, phase scales, and structural validation](milestones/m15_m15_synthetic_patterns,_phase_scales,_and_structural_validation.md)
- [M16 — M16 Lab and synchrotron CW X-ray instrument baseline](milestones/m16_m16_lab_and_synchrotron_cw_x-ray_instrument_baseline.md)
- [M17 — M17 Fundamental-parameters and detector hook foundation](milestones/m17_m17_fundamental-parameters_and_detector_hook_foundation.md)
- [M18 — M18 CW neutron instrument and correction physics](milestones/m18_m18_cw_neutron_instrument_and_correction_physics.md)
- [M19 — M19 Neutron data integration and joint weighting](milestones/m19_m19_neutron_data_integration_and_joint_weighting.md)
- [M20 — M20 TOF data model, calibration, and masks](milestones/m20_m20_tof_data_model,_calibration,_and_masks.md)
- [M21 — M21 TOF bank profile and multi-bank objective](milestones/m21_m21_tof_bank_profile_and_multi-bank_objective.md)
- [M22 — M22 TOF validation diagnostics and workflow specs](milestones/m22_m22_tof_validation_diagnostics_and_workflow_specs.md)
- [M23 — M23 Magnetic entities and magnetic scattering foundation](milestones/m23_m23_magnetic_entities_and_magnetic_scattering_foundation.md)
- [M24 — M24 Magnetic symmetry and import foundation](milestones/m24_m24_magnetic_symmetry_and_import_foundation.md)
- [M25 — M25 Magnetic joint-refinement validation and recipes](milestones/m25_m25_magnetic_joint-refinement_validation_and_recipes.md)
- [M26 — M26 EDXRD axis and calibration foundation](milestones/m26_m26_edxrd_axis_and_calibration_foundation.md)
- [M27 — M27 EDXRD detector response and correction hooks](milestones/m27_m27_edxrd_detector_response_and_correction_hooks.md)
- [M28 — M28 EDXRD high-pressure validation and documentation](milestones/m28_m28_edxrd_high-pressure_validation_and_documentation.md)
- [M29 — M29 Sequential and parametric workflow foundation](milestones/m29_m29_sequential_and_parametric_workflow_foundation.md)
- [M30 — M30 AI tool-grounded refinement foundation](milestones/m30_m30_ai_tool-grounded_refinement_foundation.md)
- [M31 — M31 Desktop and web UX foundation](milestones/m31_m31_desktop_and_web_ux_foundation.md)
- [M32 — M32 Visualization and diagnostics foundation](milestones/m32_m32_visualization_and_diagnostics_foundation.md)
- [M33 — M33 HPC and cloud execution foundation](milestones/m33_m33_hpc_and_cloud_execution_foundation.md)
- [M34 — M34 Validation and testing baseline](milestones/m34_m34_validation_and_testing_baseline.md)
- [M35 — M35 Documentation and governance baseline](milestones/m35_m35_documentation_and_governance_baseline.md)
- [M36 — M36 Benchmarking foundation and result infrastructure](milestones/m36_m36_benchmarking_foundation_and_result_infrastructure.md)
- [M37 — M37 Numerical and optimization benchmark suite](milestones/m37_m37_numerical_and_optimization_benchmark_suite.md)
- [M38 — M38 Physics workflow benchmark suite](milestones/m38_m38_physics_workflow_benchmark_suite.md)
- [M39 — M39 Storage, diagnostics, visualization, AI, and HPC benchmark suite](milestones/m39_m39_storage,_diagnostics,_visualization,_ai,_and_hpc_benchmark_suite.md)
- [M40 — M40 Benchmark regression, dashboard, and CI integration](milestones/m40_m40_benchmark_regression,_dashboard,_and_ci_integration.md)

## Workstream prompts

- [AI and Agents](workstreams/ai_and_agents.md) — 20 issues
- [Architecture](workstreams/architecture.md) — 15 issues
- [Benchmarking](workstreams/benchmarking.md) — 40 issues
- [Core Data Model](workstreams/core_data_model.md) — 20 issues
- [Diffraction Models](workstreams/diffraction_models.md) — 20 issues
- [Documentation and Governance](workstreams/documentation_and_governance.md) — 20 issues
- [EDXRD](workstreams/edxrd.md) — 15 issues
- [HPC and Cloud](workstreams/hpc_and_cloud.md) — 15 issues
- [Magnetic Refinement](workstreams/magnetic_refinement.md) — 12 issues
- [Neutron](workstreams/neutron.md) — 10 issues
- [Numerical Engine](workstreams/numerical_engine.md) — 20 issues
- [Optimization](workstreams/optimization.md) — 15 issues
- [Sequential and Parametric Workflows](workstreams/sequential_and_parametric_workflows.md) — 15 issues
- [Storage and IO](workstreams/storage_and_io.md) — 15 issues
- [TOF](workstreams/tof.md) — 15 issues
- [Testing and Validation](workstreams/testing_and_validation.md) — 20 issues
- [UX Desktop and Web](workstreams/ux_desktop_and_web.md) — 20 issues
- [Visualization](workstreams/visualization.md) — 10 issues
- [X-ray and Synchrotron](workstreams/x_ray_and_synchrotron.md) — 10 issues
