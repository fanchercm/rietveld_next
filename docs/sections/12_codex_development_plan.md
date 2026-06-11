# Part 12: Codex Development Plan

## 12.1 First 20 Milestones

The first milestones are intentionally ordered so Codex-driven work starts with schemas, tests, and reproducibility before adding scientific complexity.

### 1. Project skeleton

- **Scope:** Monorepo, CI, standards.
- **Deliverables:** Repo, formatting, linting, test harness.
- **Acceptance criteria:** CI green on Linux/macOS/Windows.

### 2. Core schema v0

- **Scope:** Project, experiment, dataset, phase, parameter schemas.
- **Deliverables:** JSON Schema + Rust/Python types.
- **Acceptance criteria:** Round-trip serialization passes.

### 3. Parameter graph

- **Scope:** Parameters, bounds, constraints, transforms.
- **Deliverables:** Graph library + Python API.
- **Acceptance criteria:** Constraint and dependency tests pass.

### 4. Basic CW XRD simulator

- **Scope:** Single phase, pseudo-Voigt, background.
- **Deliverables:** Synthetic pattern generator.
- **Acceptance criteria:** Matches analytical reference.

### 5. Least-squares engine

- **Scope:** Local optimizer wrapper, residual API.
- **Deliverables:** SciPy reference + Rust interface.
- **Acceptance criteria:** Refines synthetic cell/scale/background.

### 6. CIF import v0

- **Scope:** Parse cell, space group, atoms.
- **Deliverables:** CIF importer + validation report.
- **Acceptance criteria:** Imports standard CIF examples.

### 7. Structure factors v0

- **Scope:** X-ray nuclear structure factors.
- **Deliverables:** Kernel + tests.
- **Acceptance criteria:** Matches known reflection intensities.

### 8. GUI prototype

- **Scope:** Load data/CIF, simulate, fit.
- **Deliverables:** Tauri/React app.
- **Acceptance criteria:** End-to-end demo works.

### 9. Provenance log

- **Scope:** Replayable action log.
- **Deliverables:** JSONL action format.
- **Acceptance criteria:** GUI actions replay via CLI.

### 10. GSAS-II comparison set

- **Scope:** Benchmarks against GSAS-II examples.
- **Deliverables:** Golden dataset suite.
- **Acceptance criteria:** Results within tolerance.

### 11. Multi-phase refinement

- **Scope:** Phase scales, shared histogram.
- **Deliverables:** Multi-phase model.
- **Acceptance criteria:** Refines mixture synthetic data.

### 12. Instrument model v0

- **Scope:** CW XRD zero, wavelength, U/V/W.
- **Deliverables:** Instrument entity + calibration.
- **Acceptance criteria:** Recovers calibration.

### 13. Sequential refinement v0

- **Scope:** Series runner and parameter tables.
- **Deliverables:** Sequential workflow API.
- **Acceptance criteria:** Runs 100 synthetic datasets reproducibly.

### 14. Correlation diagnostics

- **Scope:** Covariance/correlation views.
- **Deliverables:** Backend + UI heatmap.
- **Acceptance criteria:** Flags known correlated parameters.

### 15. Neutron CW v0

- **Scope:** Scattering lengths and neutron histogram.
- **Deliverables:** Neutron model.
- **Acceptance criteria:** Matches reference neutron pattern.

### 16. TOF v0

- **Scope:** TOF axis, bank calibration, simple profile.
- **Deliverables:** TOF simulator/refiner.
- **Acceptance criteria:** Refines synthetic multi-bank TOF.

### 17. Batch/HPC v0

- **Scope:** Local parallel and Slurm adapter.
- **Deliverables:** Scheduler abstraction.
- **Acceptance criteria:** Runs 1,000 synthetic fits.

### 18. AI tool contract v0

- **Scope:** Deterministic tools for agent use.
- **Deliverables:** Tool registry + schemas.
- **Acceptance criteria:** Agent replays scripted recipe.

### 19. Guided UX v0

- **Scope:** Beginner recipe wizard.
- **Deliverables:** Stepwise refinement UI.
- **Acceptance criteria:** Novice workflow completes benchmark.

### 20. Alpha release

- **Scope:** Installers, docs, examples, validation.
- **Deliverables:** v0.1 release.
- **Acceptance criteria:** External users reproduce examples.

## 12.2 First 100 GitHub Issues

See `backlog/github_issues.md` and `backlog/github_issues.json` in the Codex package.

## 12.3 Engineering Standards

### Coding Standards

- Rust: `rustfmt`, `clippy`, no unsafe code except reviewed kernel modules.
- Python: `ruff`, `mypy`, `pytest`, typed public APIs.
- TypeScript: strict mode, ESLint, Playwright tests.
- All public APIs require docstrings and examples.
- Scientific units must be explicit.
- Floating-point tolerances must be declared in tests.

### API Standards

- Stable schemas.
- Semantic versioning.
- Every GUI action maps to public API.
- All API calls produce provenance events.
- All refinement state changes are reversible.
- Plugin APIs use capability negotiation.

### Documentation Standards

- Theory docs.
- User tutorials.
- API reference.
- Developer docs.
- Scientific validation reports.
- Known limitations.
- Citation guidance.
- Reproducibility recipes.

### CI/CD Strategy

- Linux/macOS/Windows CI.
- Rust/Python/TypeScript tests.
- Golden scientific regression tests.
- Performance benchmark CI.
- Documentation build.
- Package builds for PyPI/conda.
- Desktop installer smoke tests.
- Container image build.
- Security scanning.

### Benchmarking Strategy

Benchmarks should include profile evaluations per second, Jacobian assembly time, single-pattern refinement time, multi-phase refinement time, multi-bank TOF refinement time, sequential 1,000-pattern throughput, memory footprint, GPU speedup, and comparison to existing systems where licensing permits.
