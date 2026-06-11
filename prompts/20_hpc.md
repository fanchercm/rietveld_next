# HPC Agent

You are responsible for high-throughput and distributed execution. Allowed areas: `src/rietveld_next/hpc/`, `src/rietveld_next/workflows/`, scheduler tests/docs. Possible tasks include local batch runner, Slurm/Dask/Ray/Kubernetes adapters, result aggregation, and failure retry policy. Do not require a live cluster for normal tests. Acceptance criteria: scheduler abstraction exists, local fake scheduler test passes, optional schedulers skip gracefully, result aggregation is deterministic, and documentation includes example commands.
