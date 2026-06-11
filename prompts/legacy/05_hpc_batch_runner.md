# Codex Prompt: HPC Batch Runner

Implement the first batch and HPC execution layer.

Inputs:

- `sections/10_hpc_and_cloud_strategy.md`
- `sections/05_numerical_engine_design.md`

Deliverables:

- Local parallel batch runner.
- Result table schema.
- Parquet export placeholder or implementation.
- Slurm job-array adapter design.
- Dask/Ray adapter interfaces.

Acceptance criteria:

- 1,000 synthetic refinements run locally with reproducible seeds.
- Results are queryable by project, dataset, strategy, and metric.
- Failed refinements preserve diagnostics and do not crash the batch.
