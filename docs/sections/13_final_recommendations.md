# Part 13: Final Recommendations

## 13.1 Recommended Technology Stack

| Area | Recommendation |
|---|---|
| Core model/runtime | Rust |
| Scripting/API | Python |
| Differentiable backend | JAX |
| Reference optimizer | SciPy least-squares |
| Production optimizer | Rust sparse trust-region + optional C++/Kokkos backend |
| UI | TypeScript + React |
| Desktop | Tauri |
| Web services | Rust or Python FastAPI/gRPC services |
| Visualization | WebGL/WebGPU, Plotly-like profile plots, D3 graph views |
| Storage | JSON Schema + NeXus/HDF5 + Zarr + Parquet |
| HPC | Slurm + Dask/Ray + optional MPI/Kokkos |
| Cloud | Kubernetes + object storage |
| AI | Tool-grounded agent with deterministic refinement tools |

## 13.2 Core Language

Use Rust for the core platform and Python bindings for scientific scripting. Rust provides safe long-lived infrastructure, concurrency, reproducible serialization, plugin boundaries, and service deployment. Python remains essential for scientific users and AI/HPC orchestration.

## 13.3 Optimization Framework

- Default local optimizer: bounded sparse trust-region least squares.
- Secondary local optimizer: LM for small unconstrained problems.
- Global optimizer: differential evolution + multi-start + surrogate search.
- UQ mode: MCMC/Bayesian posterior sampling.
- Autonomous mode: recipe graph with rollback, diagnostics, and model comparison.

## 13.4 Data Model

Use a typed global parameter graph connecting projects, experiments, datasets, histograms, instruments, detector banks, phases, structures, magnetic structures, parameters, constraints, recipes, sequential studies, and provenance.

## 13.5 Storage Format

Use a hybrid project package:

- JSON for semantic model.
- NeXus/HDF5 for facility data.
- Zarr for cloud-scale arrays.
- Parquet/Arrow for parameter/result tables.
- JSONL for provenance.

## 13.6 Desktop and Web

Use Tauri + React/TypeScript for desktop and a shared React/TypeScript web frontend with REST/gRPC backend services, WebSocket streaming, and WebGL/WebGPU visualization.

## 13.7 AI Architecture

Use a three-layer AI system:

1. Rule-based scientific safety layer.
2. Tool-grounded refinement agent.
3. LLM copilot for explanation, reporting, and strategy suggestions.

No numerical result should come directly from an LLM.

## 13.8 HPC Architecture

- Local parallelism: Rust threads/Rayon.
- Batch workflows: Dask or Ray.
- HPC scheduling: Slurm.
- Tightly coupled kernels: optional MPI/Kokkos.
- Cloud: Kubernetes and object storage.
- Result database: Parquet/Arrow + metadata index.

## 13.9 Governance and License

Recommended governance: open technical steering committee, scientific working groups, facility partners, public roadmap, validation-gated releases, citation policy, and plugin certification.

Recommended license: BSD-3-Clause for the core platform.

## 13.10 Major Risks

Technical risks:

1. Underestimating profile-kernel complexity.
2. Sparse Jacobian design becoming too rigid.
3. Rust/Python/JAX interoperability complexity.
4. Packaging across facility environments.
5. GPU speedups failing for irregular small-kernel workloads.
6. Plugin API instability.
7. Data-model overengineering.
8. Desktop/web divergence.
9. HPC scheduler heterogeneity.
10. Legacy-format import burden.

Scientific risks:

1. Incorrect uncertainty estimates.
2. AI-driven overfitting.
3. Misleading low Rwp with local misfits.
4. Inadequate magnetic symmetry handling.
5. Confounding between texture, strain, size, and instrument broadening.
6. Bad EDXRD detector-response assumptions.
7. Incomplete neutron absorption/extinction corrections.
8. Incorrect joint-refinement weighting.
9. Misuse by nonexperts without validation.
10. Benchmark datasets not representative enough.

## 13.11 Ten-Year Roadmap

### Years 1-2: Foundation

Core schema, CW XRD engine, Python SDK, desktop prototype, provenance, basic sequential refinement, GSAS-II comparison benchmarks.

### Years 2-3: Neutron and TOF

CW neutron, multi-bank TOF, joint X-ray/neutron, Mantid integration, TOF calibration workflows, HPC batch runner.

### Years 3-4: Advanced Crystallography

Magnetic structures, mCIF, magnetic symmetry constraints, texture and microstructure, FPA, PDF/total-scattering interfaces.

### Years 4-5: EDXRD and In Situ

Native EDXRD, detector response functions, high-pressure workflows, parametric refinement, live beamline dashboards.

### Years 5-6: AI-Native Refinement

Validated refinement agent, strategy knowledge graph, autonomous failure recovery, report generation, AI benchmark suite.

### Years 6-7: Facility-Scale Deployment

Slurm/Ray/Dask production, cloud-native Zarr workflows, result database, multi-user web platform, beamline feedback integrations.

### Years 7-8: Differentiable and Probabilistic Refinement

AD-first kernels, Bayesian model comparison, MCMC/HMC workflows, surrogate-assisted global refinement, active learning for experiments.

### Years 8-9: Multi-Modal Digital Twin

Diffraction + PDF + spectroscopy + microscopy constraints, materials digital twin models, cross-instrument parameter priors, automated phase-transition discovery.

### Years 9-10: Autonomous Diffraction Ecosystem

Closed-loop beamline experimentation, community plugin marketplace, certified scientific workflows, reproducible refinement archives, AI-assisted publication pipelines.
