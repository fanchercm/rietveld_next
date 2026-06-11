# Codex Prompt: Enforce `src/` Layout Guardrails

Update or review repository work so implementation code lands only under `src/`.

Requirements:

- Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, or `web/`.
- Place Rust core code under `src/rietveld_next/core/rn-core-rs/`.
- Place Python SDK code under `src/rietveld_next/core/rn-sdk-python/`.
- Place schemas used by implementation under `src/rietveld_next/core/rn-schema/`, while input/reference schemas may remain in `schemas/` and `inputs/`.
- Place UX implementation under `src/rietveld_next/desktop/` and `src/rietveld_next/web/`.
- Keep top-level `docs/`, `benchmarks/`, `examples/`, and `tests/` as non-source support areas.
- Update CI paths and workspace manifests to reference `src/...` packages.

Acceptance criteria:

- No top-level source package directories are created.
- Workspace manifests reference `src/rietveld_next/core/rn-core-rs`, `src/rietveld_next/core/rn-sdk-python`, `src/rietveld_next/desktop`, and `src/rietveld_next/web` as appropriate.
- Existing tests and validation scripts continue to pass.
