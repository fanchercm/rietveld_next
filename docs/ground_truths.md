# Ground Truths

## Repository Hygiene

- `.codegraph/` is generated local Codegraph index and daemon state; it is
  ignored by Git and is not project source.

## Core Data Model

- The current core data model implementation is metadata-only and lives under
  `src/rietveld_next/core/model/`.
- `schemas/project.schema.json` accepts the required project fields
  `schema_version`, `id`, `experiments`, `phases`, and `parameters` on the
  `1.0.x` compatibility line.
- Parameter paths are serialized as stable slash-delimited addresses such as
  `phase/phase1/crystal_structure/cell/a`.
- Package-local tests live under `src/rietveld_next/core/model/tests/` to avoid
  creating a forbidden top-level `tests/` directory before the source layout
  milestone is complete.
- Schema-backed serialization helpers live under
  `src/rietveld_next/core/schema/` and validate project JSON against
  `schemas/project.schema.json`.
- The current schema compatibility line is `1.0.x`; prompt 04 changes are
  additive and do not intentionally break minimal valid `1.0.x` payloads.
- Repository boundary checks live under `src/rietveld_next/core/architecture/`
  and are exercised by package-local tests under
  `src/rietveld_next/core/architecture/tests/`.
- The current Batch A architecture boundary assessment is documented in
  [architecture_boundary_report.md](architecture_boundary_report.md).
- The canonical package-tree document is `docs/PACKAGE_TREE.md`; a root-level
  `PACKAGE_TREE.md` is treated as a stale location by the boundary checker.
- `backend_corpus/` is a top-level validation support directory for public
  backend corpus manifests and download scripts; it is not an implementation
  source package.
- `backend_corpus/` currently contains public GSAS-II fixture files plus a
  downloader script, but no `__init__.py` package marker.
- M01 architecture foundation helpers live in
  `src/rietveld_next/core/architecture/foundation.py` and cover shared
  architecture errors, JSON configuration loading, provenance event envelopes,
  environment capture, API stability levels, feature flags, and release
  artifact manifests.
- M01 design docs now define workspace build conventions, plugin capability
  metadata, and the ADR workflow in `docs/workspace_build_conventions.md`,
  `docs/plugin_capability_model.md`, `docs/adr_workflow.md`, and
  `architecture/0000-adr-template.md`.
- M01 completion evidence for closing issues #1-15 is recorded in
  [m01_completion_report.md](m01_completion_report.md), which maps each issue to
  committed code, docs, and validation evidence.

## Numerical Kernels

- The first numerical reference kernels are dependency-free Python functions in
  `src/rietveld_next/diffraction/` and `src/rietveld_next/optimization/`.
- `gaussian_profile` implements an area-scaled Gaussian using FWHM:
  `area * sqrt(4 ln(2) / pi) / fwhm * exp(-4 ln(2) * ((x-center)/fwhm)^2)`.
- `residual_vector` uses `observed - calculated`, or
  `(observed - calculated) / sigma` when positive standard uncertainties are
  supplied.
- These kernels are tested on analytic/synthetic cases only and do not yet
  constitute cross-software scientific validation.
- Batch B profile helpers now include area-scaled Lorentzian,
  pseudo-Voigt, Thompson-Cox-Hastings pseudo-Voigt approximation, finite peak
  window selection, and deterministic reflection batching in
  `src/rietveld_next/diffraction/profiles.py`.
- X-ray Batch B helpers currently cover wavelength validation and Bragg-law
  two-theta calculation in `src/rietveld_next/xray/`; they do not yet include
  X-ray form-factor tables or instrument models.
- Neutron Batch B helpers currently include a small provenance-labeled bound
  coherent scattering-length subset in `src/rietveld_next/neutron/`; the table
  is intentionally incomplete and unsupported isotopes fail clearly. `H`/`nat H`
  represent the natural hydrogen row, while `1H` uses the isotope-specific row.
- Optional backend benchmark hooks live under `src/rietveld_next/benchmarks/`.
  JAX is imported only inside the opt-in runner and missing JAX returns a
  structured skipped result; no Rust benchmark executable exists yet.

## Optimization

- Batch C optimization infrastructure lives under
  `src/rietveld_next/optimization/` and remains dependency-free.
- Objective evaluations are structured by `ObjectiveEvaluation`; invalid model
  states use `status="invalid"` with diagnostic metadata and a large finite
  penalty rather than non-JSON infinity.
- Parameter scaling and bounded transforms are generic and do not encode
  diffraction-specific assumptions.
- `coordinate_search_minimize` is a deterministic local optimizer for synthetic
  tests, smoke benchmarks, and adapter validation; it is not a production
  least-squares, trust-region, or Levenberg-Marquardt implementation.
- The local optimizer benchmark hook lives in
  `src/rietveld_next/benchmarks/optimizer.py` and reports convergence metrics
  through the shared benchmark result record.

## Batch E Foundations

- Workflow replay primitives live in `src/rietveld_next/workflows/` and emit
  ordered action records suitable for provenance logs.
- AI integration is limited to deterministic tool contracts and action logging
  in `src/rietveld_next/ai/`; no LLM calls or autonomous data mutation are
  implemented in this foundation.
- HPC support is limited to a scheduler abstraction and deterministic local
  scheduler in `src/rietveld_next/hpc/`; no live cluster adapter is included.
- UI work is framework-neutral and lives in `src/rietveld_next/desktop/`,
  where view commands can be converted into replayable workflow steps.
- Visualization transforms live in `src/rietveld_next/visualization/` and
  prepare profile/difference display series without calculating scientific model
  values.

## Batch D Foundations

- TOF histogram-axis helpers live in `src/rietveld_next/tof/` and store
  strictly increasing positive bin edges in microseconds with optional
  detector-bank metadata.
- EDXRD histogram-axis helpers live in `src/rietveld_next/edxrd/` and store
  strictly increasing positive energy bin edges in keV; the initial calibration
  helper supports a linear channel-to-energy edge model only.
- Magnetic moment entities live in `src/rietveld_next/neutron/magnetic/` and
  record three components in Bohr magnetons plus an explicit coordinate frame.
- The initial storage reader lives in `src/rietveld_next/storage/` and loads
  directory-backed packages from `project.json` plus optional `manifest.json`
  without creating, overwriting, or repairing user files.
- Unit test conventions are documented in
  [unit_test_conventions.md](unit_test_conventions.md); package-local tests
  remain under `src/rietveld_next/**/tests/` to satisfy the current source
  layout guardrail.
