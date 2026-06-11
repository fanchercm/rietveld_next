# Repository Boundaries

## Source-code root

All implementation source code lives under `src/`. Top-level directories outside `src/` are reserved for benchmarks, documentation, examples, tests, schemas, CI files, project configuration, and generated artifacts.

## Dependency direction

`src/core` must not depend on UI, AI, or workflow packages. Numerical kernels may depend on core domain abstractions but should not know about desktop/web implementation details. UX packages must call public APIs only. AI tools must call deterministic workflow and engine APIs only.

## Public API rule

Every command exposed in desktop/web must exist in the Python SDK and CLI. Every state change must produce a provenance event.

## Plugin rule

Plugins must declare capabilities: supported radiation types, axis types, derivative support, parameter names, units, bounds, and validation functions.

## Codex placement rule

When Codex creates or modifies implementation files, it must place them in the appropriate `src/<package>/...` subtree. Tests should live in `tests/` unless they are package-local unit tests required by a language ecosystem, such as Rust crate tests under `src/core/rn-core-rs/tests/`.
