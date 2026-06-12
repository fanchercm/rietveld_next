"""Opt-in benchmark helpers for numerical kernels."""

from rietveld_next.benchmarks.datasets import (
    GaussianPeak,
    ProfileDatasetPreset,
    SyntheticProfileDataset,
    generate_synthetic_gaussian_profile_dataset,
    profile_dataset_presets,
)
from rietveld_next.benchmarks.jax_gaussian import run_jax_gaussian_microbenchmark
from rietveld_next.benchmarks.optimizer import (
    run_automatic_differentiation_benchmark,
    run_global_multistart_benchmark,
    run_local_optimizer_benchmark,
    run_optimizer_scaling_benchmark,
    run_sparse_jacobian_assembly_benchmark,
)
from rietveld_next.benchmarks.physics_proxies import (
    run_edxrd_detector_response_proxy_benchmark,
    run_magnetic_structure_factor_proxy_benchmark,
    run_multi_bank_tof_profile_proxy_benchmark,
    run_neutron_scattering_lookup_proxy_benchmark,
)
from rietveld_next.benchmarks.results import (
    BENCHMARK_RESULT_SCHEMA_VERSION,
    BenchmarkResult,
    BenchmarkTiming,
    benchmark_result_schema,
    skipped_benchmark,
    validate_benchmark_result_dict,
)
from rietveld_next.benchmarks.storage_visualization_diagnostics import (
    DecimatedProfile,
    ResidualDiagnosticReport,
    compute_residual_diagnostics,
    decimate_profile_extrema,
    run_project_package_storage_benchmark,
    run_residual_diagnostics_benchmark,
    run_visualization_decimation_benchmark,
)
from rietveld_next.benchmarks.taxonomy import (
    BenchmarkFamily,
    BenchmarkIdentity,
    BenchmarkKind,
    BenchmarkWorkstream,
    benchmark_families,
    build_benchmark_id,
    parse_benchmark_id,
)
from rietveld_next.benchmarks.workflow_ai_hpc import (
    build_deterministic_tool_registry,
    run_ai_tool_call_overhead_benchmark,
    run_sequential_refinement_workflow_overhead_benchmark,
    run_slurm_job_array_packaging_benchmark,
)

__all__ = [
    "BENCHMARK_RESULT_SCHEMA_VERSION",
    "BenchmarkFamily",
    "BenchmarkIdentity",
    "BenchmarkKind",
    "BenchmarkResult",
    "BenchmarkTiming",
    "BenchmarkWorkstream",
    "DecimatedProfile",
    "GaussianPeak",
    "ProfileDatasetPreset",
    "ResidualDiagnosticReport",
    "SyntheticProfileDataset",
    "benchmark_families",
    "benchmark_result_schema",
    "build_benchmark_id",
    "build_deterministic_tool_registry",
    "compute_residual_diagnostics",
    "decimate_profile_extrema",
    "generate_synthetic_gaussian_profile_dataset",
    "parse_benchmark_id",
    "profile_dataset_presets",
    "run_ai_tool_call_overhead_benchmark",
    "run_automatic_differentiation_benchmark",
    "run_edxrd_detector_response_proxy_benchmark",
    "run_global_multistart_benchmark",
    "run_jax_gaussian_microbenchmark",
    "run_local_optimizer_benchmark",
    "run_magnetic_structure_factor_proxy_benchmark",
    "run_multi_bank_tof_profile_proxy_benchmark",
    "run_neutron_scattering_lookup_proxy_benchmark",
    "run_optimizer_scaling_benchmark",
    "run_project_package_storage_benchmark",
    "run_residual_diagnostics_benchmark",
    "run_sequential_refinement_workflow_overhead_benchmark",
    "run_slurm_job_array_packaging_benchmark",
    "run_sparse_jacobian_assembly_benchmark",
    "run_visualization_decimation_benchmark",
    "skipped_benchmark",
    "validate_benchmark_result_dict",
]
