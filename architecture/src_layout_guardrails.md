# Source Layout Update: `src/` Is the Implementation Root

The repository now uses `src/` as the canonical home for implementation source code.

## Rule

All generated source code must land under:

```text
rietveld-next/src/
```

Examples:

- Rust core crate: `src/rietveld_next/core/rn-core-rs/`
- Python SDK: `src/rietveld_next/core/rn-sdk-python/`
- Diffraction kernels: `src/rietveld_next/diffraction/`
- X-ray models: `src/rietveld_next/xray/`
- Neutron models: `src/rietveld_next/neutron/`
- TOF models: `src/rietveld_next/tof/`
- EDXRD models: `src/rietveld_next/edxrd/`
- Optimization code: `src/rietveld_next/optimization/`
- Workflow code: `src/rietveld_next/workflows/`
- AI tools and agents: `src/rietveld_next/ai/`
- HPC adapters: `src/rietveld_next/hpc/`
- Desktop application source: `src/rietveld_next/desktop/`
- Web application source: `src/rietveld_next/web/`

Top-level support directories such as `docs/`, `backlog/`, `github/`, `prompts/`, `schemas/`, `scaffold/`, `validation/`, and `backend_corpus/` remain outside `src/`.

`backend_corpus/` is reserved for public backend test fixtures, corpus manifests,
and corpus acquisition scripts. It must not contain importable implementation
packages or runtime source code.

## Codex instruction

Before creating files for any issue or milestone, Codex should resolve the destination package under `src/rietveld_next/` and avoid creating top-level source packages such as `core/`, `diffraction/`, `optimization/`, `desktop/`, or `web/`.
