# Source Layout Update: `src/` Is the Implementation Root

The repository now uses `src/` as the canonical home for implementation source code.

## Rule

All generated source code must land under:

```text
rietveld-next/src/
```

Examples:

- Rust core crate: `src/core/rn-core-rs/`
- Python SDK: `src/core/rn-sdk-python/`
- Diffraction kernels: `src/diffraction/`
- X-ray models: `src/xray/`
- Neutron models: `src/neutron/`
- TOF models: `src/tof/`
- EDXRD models: `src/edxrd/`
- Optimization code: `src/optimization/`
- Workflow code: `src/workflows/`
- AI tools and agents: `src/ai/`
- HPC adapters: `src/hpc/`
- Desktop application source: `src/desktop/`
- Web application source: `src/web/`

Top-level directories such as `docs/`, `benchmarks/`, `examples/`, and `tests/` remain outside `src/`.

## Codex instruction

Before creating files for any issue or milestone, Codex should resolve the destination package under `src/` and avoid creating top-level source packages such as `core/`, `diffraction/`, `optimization/`, `desktop/`, or `web/`.
