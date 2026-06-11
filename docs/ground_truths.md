# Ground Truths

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
