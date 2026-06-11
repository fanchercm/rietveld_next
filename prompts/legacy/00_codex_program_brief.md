# Codex Program Brief

You are implementing Rietveld Next, a next-generation Rietveld refinement platform. Read `report/REPORT.md`, `inputs/scientific_requirements.md`, `inputs/architecture_input.md`, and `inputs/repository_boundaries.md` before writing code.

Primary goals:

- Build a Rust core with a typed scientific domain model.
- Expose a Python SDK for all operations.
- Make every state change provenance-recorded.
- Implement numerical kernels behind stable interfaces.
- Keep UX, AI, and HPC layers dependent on public APIs only.

Start by implementing Milestone 1 from `backlog/milestones.md`. Do not skip tests, schemas, or documentation.
