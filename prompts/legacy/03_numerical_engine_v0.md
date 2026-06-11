# Codex Prompt: Numerical Engine v0

Implement a minimal scientific engine capable of synthetic CW XRD simulation and least-squares refinement.

Inputs:

- `sections/05_numerical_engine_design.md`
- `sections/03_recommended_architecture.md`
- `backlog/milestones.md`

Scope:

- Pseudo-Voigt profile.
- Polynomial background.
- Single-phase synthetic reflections.
- Parameter vector mapping from model graph.
- Residual vector calculation.
- SciPy-backed reference optimizer in Python.
- Rust trait/interface for future production optimizers.

Acceptance criteria:

- Synthetic scale, background, zero, and cell shift can be recovered.
- All output parameters include uncertainty placeholders.
- Refinement action is logged to provenance.
- Golden test fixture is stored under `tests/golden/`.
