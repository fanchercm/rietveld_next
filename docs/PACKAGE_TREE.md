# Rietveld Next Package Tree

This document is the canonical package-tree reference for agents and
contributors. The root-level `PACKAGE_TREE.md` path is intentionally not used.

## Top-Level Layout

```text
rietveld_next/
├── AGENTS.md
├── README.md
├── MANIFEST.json
├── architecture/
├── backend_corpus/
├── backlog/
├── docs/
├── github/
├── prompts/
├── scaffold/
├── schemas/
├── src/
└── validation/
```

## Directory Responsibilities

- `src/` contains all implementation source and package-local tests.
- `src/rietveld_next/core/model/` contains typed core project entities.
- `src/rietveld_next/core/schema/` contains schema-backed project
  serialization helpers.
- `src/rietveld_next/core/architecture/` contains source-layout and dependency
  boundary checks.
- `src/rietveld_next/diffraction/` contains dependency-free diffraction
  reference kernels.
- `src/rietveld_next/xray/` contains X-ray physics reference data and helpers.
- `src/rietveld_next/neutron/` contains neutron physics reference data and
  helpers.
- `src/rietveld_next/optimization/` contains dependency-free optimization
  reference interfaces.
- `src/rietveld_next/workflows/` contains replayable workflow primitives.
- `src/rietveld_next/ai/` contains deterministic AI tool-boundary primitives.
- `src/rietveld_next/hpc/` contains scheduler abstraction primitives.
- `src/rietveld_next/desktop/` contains framework-neutral UI view models.
- `src/rietveld_next/visualization/` contains display-oriented data
  transforms.
- `src/rietveld_next/benchmarks/` contains opt-in benchmark infrastructure and
  smoke fixtures.
- `docs/` contains developer and user documentation, including this canonical
  package tree.
- `architecture/` contains architecture notes and guardrail documents.
- `schemas/` contains JSON Schema files for persistent project metadata.
- `backlog/` contains canonical issue and milestone files.
- `github/` contains GitHub import payloads generated from the backlog.
- `prompts/` contains program, milestone, issue, workstream, and batch-agent
  prompts.
- `backend_corpus/` contains public backend validation corpus manifests and
  download scripts. It is not an implementation package.
- `validation/` contains validation planning documents.
- `scaffold/` contains scaffold notes and non-runtime setup artifacts.

## Guardrails

- Do not create implementation source outside `src/`.
- Do not create top-level implementation or test directories such as `core/`,
  `diffraction/`, `optimization/`, `benchmarks/`, or `tests/`.
- Keep tests package-local under `src/rietveld_next/.../tests/` unless a future
  documented build-system decision changes the test layout.
- Keep batch-agent prompts directly under `prompts/`; there is intentionally no
  `prompts/batch_agents/` directory.
- Use `docs/PACKAGE_TREE.md` as the only canonical package-tree path.
