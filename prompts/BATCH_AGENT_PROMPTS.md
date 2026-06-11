# Batch Agent Prompts

This folder contains prompts for safely running batches of Codex-style agents on the `rietveld-next` codebase.

## Canonical instructions

All agents should read:

1. `AGENTS.md`
2. `docs/PACKAGE_TREE.md`
3. `backlog/issues.md`
4. `backlog/milestones.md`
5. The assigned issue or milestone prompt
6. The relevant batch-agent prompt in this folder

## Recommended batches

### Batch A: safe foundation

- Architecture Boundary Agent
- Core Data Model Agent
- Schema and Serialization Agent
- Documentation Agent
- Testing and Validation Agent

### Batch B: independent numerical kernels

- Numerical Kernel Agent
- Profile Function Agent
- X-ray Physics Agent
- Neutron Physics Agent
- Rust Backend Benchmark Agent
- JAX Backend Agent

### Batch C: optimization

- Optimization Agent for objective interface
- Optimization Agent for bounds/transforms
- Optimization Agent for local optimizer
- Optimization Agent for diagnostics
- Benchmark Agent for optimizer benchmarks

### Batch D: specialized physics

- TOF Agent
- EDXRD Agent
- Magnetic Refinement Agent
- Storage and IO Agent
- Testing and Validation Agent

### Batch E: workflows, HPC, AI, UX

- Workflow Agent
- HPC Agent
- AI Agent Integration Developer
- UX Agent
- Visualization Agent

## Critical guardrails

Implementation source belongs under `src/`. The canonical package tree document belongs at `docs/PACKAGE_TREE.md`. Expensive benchmarks must be opt-in. Scientific formulas require tests and documentation.
