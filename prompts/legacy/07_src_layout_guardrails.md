# Codex Prompt: Enforce `src/` Layout Guardrails

Update or review repository work so implementation code lands only under `src/`.

Requirements:

- Do not create top-level implementation directories such as `core/`, `diffraction/`, `xray/`, `neutron/`, `tof/`, `edxrd/`, `optimization/`, `workflows/`, `ai/`, `hpc/`, `desktop/`, or `web/`.
- Place Rust core code under `src/core/rn-core-rs/`.
- Place Python SDK code under `src/core/rn-sdk-python/`.
- Place schemas used by implementation under `src/core/rn-schema/`, while input/reference schemas may remain in `schemas/` and `inputs/`.
- Place UX implementation under `src/desktop/` and `src/web/`.
- Keep top-level `docs/`, `benchmarks/`, `examples/`, and `tests/` as non-source support areas.
- Update CI paths and workspace manifests to reference `src/...` packages.

Acceptance criteria:

- No top-level source package directories are created.
- Workspace manifests reference `src/core/rn-core-rs`, `src/core/rn-sdk-python`, `src/desktop`, and `src/web` as appropriate.
- Existing tests and validation scripts continue to pass.
