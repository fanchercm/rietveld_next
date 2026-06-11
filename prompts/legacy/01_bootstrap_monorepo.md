# Codex Prompt: Bootstrap Monorepo

Create the initial `rietveld-next/` monorepo from `inputs/repo_tree.txt`. Treat `src/` as the canonical implementation root.

Requirements:

- Rust workspace for `src/core/rn-core-rs`.
- Python package skeleton for `src/core/rn-sdk-python`.
- TypeScript workspace placeholders for `src/desktop` and `src/web`.
- `schemas/` package or folder with `project.schema.json`.
- GitHub Actions CI placeholder for Rust, Python, TypeScript, and docs.
- `docs/architecture/adr/` initialized with ADRs from `adr/`.
- Root README explaining architecture and development flow.
- No numerical implementation yet; focus on build, lint, test, and boundaries.

Acceptance criteria:

- `cargo test` passes.
- `pytest` passes.
- TypeScript lint placeholder passes.
- Schema file is copied into the repo and validated by a test.
