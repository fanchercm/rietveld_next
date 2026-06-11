# Architecture Input for Codex

Build Rietveld Next as a layered platform:

1. Storage layer: JSON Schema, NeXus/HDF5, Zarr, Arrow/Parquet, JSONL provenance.
2. Core domain layer: typed Project, Experiment, Dataset, Histogram, Instrument, DetectorBank, Phase, Structure, MagneticStructure, Parameter, Constraint, Strategy, SequentialStudy.
3. Numerical engine layer: profile kernels, structure factors, corrections, sparse Jacobian, optimizer interface.
4. Workflow layer: sequential, parametric, batch, beamline, HPC.
5. AI layer: deterministic tool contracts, refinement agent, copilot, audit log.
6. UX layer: Tauri desktop, React web, notebook/CLI.

Core language: Rust.
Scripting language: Python.
UI language: TypeScript.
Differentiable backend: JAX.
HPC integration: Slurm + Dask/Ray + optional Kokkos/MPI.


## Source layout update

All implementation source code now lands under `src/`. Use `src/rietveld_next/core`, `src/rietveld_next/diffraction`, `src/rietveld_next/xray`, `src/rietveld_next/neutron`, `src/rietveld_next/tof`, `src/rietveld_next/edxrd`, `src/rietveld_next/optimization`, `src/rietveld_next/workflows`, `src/rietveld_next/ai`, `src/rietveld_next/hpc`, `src/rietveld_next/desktop`, and `src/rietveld_next/web` for generated source files.
