# Repository Boundaries

## Source-code root

All implementation source code lives under `src/`. Top-level directories outside
`src/` are reserved for documentation, schemas, prompts, backlog files, GitHub
import payloads, scaffold notes, validation planning, public backend corpus
fixtures, CI files, and project configuration. Do not create top-level
implementation or test directories such as `core/`,
`diffraction/`, `optimization/`, `benchmarks/`, or `tests/`.

## Dependency direction

`src/rietveld_next/core` must not depend on UI, AI, or workflow packages. Numerical kernels may depend on core domain abstractions but should not know about desktop/web implementation details. UX packages must call public APIs only. AI tools must call deterministic workflow and engine APIs only.

## Public API rule

Every command exposed in desktop/web must exist in the Python SDK and CLI. Every state change must produce a provenance event.

## Plugin rule

Plugins must declare capabilities: supported radiation types, axis types, derivative support, parameter names, units, bounds, and validation functions.

## Codex placement rule

When Codex creates or modifies implementation files, it must place them in the
appropriate `src/rietveld_next/<package>/...` subtree. Tests should be
package-local under `src/rietveld_next/.../tests/` unless a future build-system
decision explicitly introduces a different, documented test layout.
