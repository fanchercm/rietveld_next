# Codex Prompt: AI Tool Contracts

Implement deterministic tool contracts for AI-assisted refinement.

Inputs:

- `sections/09_ai_native_refinement.md`
- `inputs/architecture_input.md`

Deliverables:

- JSON schemas for each AI-callable tool.
- Tool registry with no direct LLM dependency.
- Tools for import, validate, simulate, set flags, run refinement, diagnose residuals, rollback, compare models, and generate report.
- Provenance event for every tool call.

Acceptance criteria:

- A scripted sequence can call tools and replay without an LLM.
- Tools return structured diagnostics, not free text only.
- Unsafe or nonphysical actions are rejected with typed errors.
