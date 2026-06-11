# Part 10: HPC and Cloud Strategy

## 10.1 Execution Targets

| Target | Execution model | Main use case |
|---|---|---|
| Local desktop | Rust threads/Rayon + Python SDK + local cache | Routine refinement, teaching, small sequential studies |
| Workstation | Multi-process + optional GPU/JAX | Multi-start, large images, moderate batch |
| HPC cluster | Slurm job arrays + Ray/Dask + shared object store | Thousands of refinements and beamline campaigns |
| Cloud | Kubernetes + object storage + service APIs | Collaborative analysis and elastic high-throughput |

## 10.2 MPI, Dask, Ray, Kubernetes, Slurm

| Technology | Strengths | Weaknesses | Recommendation |
|---|---|---|---|
| MPI | Best for tightly coupled HPC kernels | Harder for dynamic Python-heavy orchestration | Specialized kernels only |
| Dask | Python-native distributed arrays/tasks | Scheduler overhead for tiny tasks | Data-parallel refinement batches |
| Ray | Actor/task model, good for ML/agents | Less traditional at some HPC centers | Autonomous services and global search |
| Slurm | Standard HPC scheduler | Not a workflow system by itself | Required HPC integration layer |
| Kubernetes | Cloud-native scaling and APIs | Storage/security complexity | Cloud and facility service deployment |

## 10.3 Beamline Automation

Beamline mode should support live data ingestion, reduction hooks from Mantid/pyFAI/beamline pipelines, initial refinement from previous point, drift detection, phase-change detection, real-time dashboards, autonomous suggestions, and facility-safe feedback APIs.
