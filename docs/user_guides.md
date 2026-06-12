# Rietveld Next User and Developer Guides

Purpose: provide a concise operating guide for issues #268-#281. These sections
summarize how the current prototype should be used, extended, and validated
without claiming full scientific validation.

Current status: the repository contains a `src/`-first Python prototype with
package-local tests, reference kernels, schema/model helpers, optimization
interfaces, modality-specific packages, workflow primitives, AI tool-boundary
helpers, HPC scheduler abstractions, and opt-in benchmark/validation support.
Use this guide with [PACKAGE_TREE.md](PACKAGE_TREE.md), [report.md](report.md),
[core_data_model.md](core_data_model.md), [numerical_kernels.md](numerical_kernels.md),
[optimization.md](optimization.md), and [validation_baseline.md](validation_baseline.md).

Non-goals: this guide is not a scientific validation report, a user manual for a
finished application, or a promise that all Rietveld modalities are production
complete. Where validation data is absent, treat examples as conceptual unless
the command is explicitly marked runnable.

## Architecture Overview

Scope: orient contributors to the current package boundaries and review path.
All implementation code belongs under `../src/rietveld_next/`; top-level
directories are documentation, schema, backlog, validation-planning, or scaffold
areas only.

Primary layers:

- `../src/rietveld_next/core/` owns typed project entities, schema-backed
  serialization, migration helpers, layout checks, and dependency guardrails.
- `../src/rietveld_next/storage/` owns project-package IO and provenance logs.
- `../src/rietveld_next/diffraction/`, `../src/rietveld_next/structure/`,
  `../src/rietveld_next/xray/`, `../src/rietveld_next/neutron/`,
  `../src/rietveld_next/tof/`, and `../src/rietveld_next/edxrd/` own scientific
  reference calculations and modality-specific helpers.
- `../src/rietveld_next/optimization/` owns residual/objective interfaces,
  optimizer adapters, parameter transforms, diagnostics, and reproducibility
  helpers.
- `../src/rietveld_next/workflows/`, `../src/rietveld_next/ai/`,
  `../src/rietveld_next/hpc/`, `../src/rietveld_next/desktop/`, and
  `../src/rietveld_next/visualization/` own orchestration, AI boundaries,
  scheduler abstractions, view models, and display transforms.
- `../src/rietveld_next/benchmarks/` and `../src/rietveld_next/validation/`
  provide opt-in measurement and lightweight baseline helpers.

Development rule: when adding a feature, first identify the owning package,
then add the smallest package-local tests under that package. Do not add
parallel top-level packages such as `optimization/`, `benchmarks/`, or `tests/`.

Runnable validation:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next -p 'test*.py'
```

Known limitations: package boundaries are documented and partly covered by
architecture tests, but this guide does not certify every scientific model.
Scientific claims still require issue-specific validation evidence.

## Src Layout Developer Guide

Scope: explain where new work belongs.

Use this decision checklist:

1. Persistent project metadata or schema migrations go in
   `../src/rietveld_next/core/schema/` and the matching schema file under
   `../schemas/` only when the schema itself is intentionally versioned.
2. Domain entities go in `../src/rietveld_next/core/model/`.
3. Numerical kernels go in the most specific scientific package, not in UI,
   workflow, or AI packages.
4. Optimizer interfaces and result diagnostics go in
   `../src/rietveld_next/optimization/`.
5. Tests stay package-local under `../src/rietveld_next/<package>/tests/`.
6. Documentation goes in `../docs/`; planning documents may live in
   `../validation/`, `../prompts/`, or `../scaffold/` when that is their
   established purpose.

Conceptual example:

```text
Add an EDXRD calibration helper:
1. Put implementation in src/rietveld_next/edxrd/.
2. Put tests in src/rietveld_next/edxrd/tests/.
3. Document assumptions, units, and limitations in docs/.
4. Do not create top-level edxrd/ or tests/.
```

Validation command for layout drift:

```bash
find . -maxdepth 1 -type d \( -name core -o -name diffraction -o -name xray -o -name neutron -o -name tof -o -name edxrd -o -name optimization -o -name workflows -o -name ai -o -name hpc -o -name desktop -o -name web -o -name benchmarks -o -name tests \) -print
```

Expected output is empty.

## Data Model Guide

Scope: describe how project data should be represented and persisted.

Core data should be typed, schema-backed, and deterministic. Persistent formats
must be versioned; public schema changes require documentation and migration
notes. Large numerical arrays should be referenced through storage adapters
rather than embedded directly in JSON metadata.

Data-model checklist:

- Record units, shapes, dtype expectations, bounds, and provenance where they
  affect scientific interpretation.
- Keep parameter paths stable so optimizers, constraints, histories, and user
  interfaces can reference the same quantity.
- Validate at package boundaries and return explicit errors for malformed or
  unsupported inputs.
- Preserve deterministic serialization order for reproducible diffs and
  package replay.
- Add round-trip tests for new persistent fields.

Conceptual example:

```python
# Conceptual only: use the concrete model/schema APIs in src/rietveld_next/core/.
project = load_project_package("example.rnx")
validate_project_schema(project.metadata)
save_project_package(project, "example-roundtrip.rnx")
```

Known limitations: the model foundation exists, but external format coverage,
migrations, and full cross-software validation must be checked per feature.

## Numerical Engine Theory Guide

Scope: orient contributors to numerical assumptions without substituting for a
derivation or validation paper.

Numerical calculations should be organized around small, testable kernels:
profile functions, reflection generation, corrections, residual vectors,
Jacobian blocks, and diagnostics. Each kernel should state its input domain,
units, normalization convention, and expected numerical tolerance.

Required documentation for a scientific kernel:

- Formula or algorithm name, with reference when applicable.
- Input shapes, dtype assumptions, units, and bounds.
- Output shape, units, and normalization.
- Failure modes for invalid physical states.
- Known-value, edge-case, and regression tests.
- Tolerance rationale and whether it is absolute, relative, or mixed.

Known limitations: current reference kernels and tests are lightweight. They
support development and regression detection but do not establish broad
facility-grade validation across all instruments and sample classes.

## Optimization Guide

Scope: explain safe use of local/global optimization infrastructure.

Optimization code should separate residual construction, parameter transforms,
optimizer execution, result reporting, and model mutation. Refinement must
report objective values, iteration counts, termination reasons, parameter
shifts, warnings, and rollback information where available.

Use these defaults:

- Prefer deterministic local refinement for normal CI and examples.
- Log seeds, bounds, candidate lists, and final local-refinement status for any
  stochastic or multi-start path.
- Treat convergence as a numerical result, not proof of physical correctness.
- Report covariance/correlation diagnostics with parameter labels and units.
- Warn on singular, ill-conditioned, underconstrained, or nonphysical results.

Runnable smoke test:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next/optimization -p 'test*.py'
```

Known limitations: global, Bayesian, and MCMC-style workflows may be placeholders
or optional depending on installed dependencies. Expensive global tests are
opt-in and should not be added to default CI without an explicit issue.

## TOF Refinement Guide

Scope: provide contributor rules for time-of-flight diffraction work.

TOF features must document the conversion between time, d-spacing, and any
instrument calibration parameters they use. Profile functions should state
whether peak asymmetry, moderator pulse shape, detector offsets, and bank
geometry are modeled, approximated, or unsupported.

Implementation checklist:

- Put TOF code under `../src/rietveld_next/tof/`.
- Validate units for time channels, flight path, d-spacing, and calibration
  coefficients.
- Include synthetic known-value tests for peak position and profile behavior.
- Record instrument-bank provenance in project metadata or storage references.

Known limitations: do not treat TOF support as fully validated until reference
datasets and instrument-specific comparisons are attached to the relevant issue.

## Neutron Refinement Guide

Scope: cover neutron-specific diffraction behavior.

Neutron workflows must distinguish coherent scattering lengths, absorption,
isotopic assumptions, magnetic contributions, and instrument modality. Any
reference tables need citation/provenance metadata and versioning.

Implementation checklist:

- Put neutron code under `../src/rietveld_next/neutron/`.
- Keep magnetic-specific work under `../src/rietveld_next/neutron/magnetic/`.
- Validate scattering table lookup inputs and missing-isotope behavior.
- Document whether nuclear-only or nuclear-plus-magnetic scattering is being
  calculated.

Known limitations: current neutron helpers should be treated as reference
infrastructure unless issue-specific validation proves a broader claim.

## Magnetic Refinement Guide

Scope: define safe boundaries for magnetic scattering features.

Magnetic refinement must expose assumptions about spin orientation, propagation
vectors, magnetic form factors, symmetry constraints, and coupling to nuclear
structure. It must not silently infer magnetic models from nuclear models.

Implementation checklist:

- Store magnetic parameters with explicit units and parameter paths.
- Report unsupported symmetry, missing form-factor data, and inconsistent
  magnetic moment constraints as warnings or errors.
- Add tests for zero-moment, single-site, and invalid-constraint cases.
- Keep expert override possible, but log overrides in provenance.

Known limitations: full magnetic validation requires reference structures and
cross-software comparisons; this guide only defines implementation behavior.

## EDXRD Guide

Scope: cover energy-dispersive X-ray diffraction support.

EDXRD work must document the energy calibration model, detector channel units,
fixed-angle assumptions, and uncertainty propagation. Calibration and peak
position helpers belong under `../src/rietveld_next/edxrd/`.

Implementation checklist:

- Validate channel index ranges, energy units, calibration coefficients, and
  detector angle metadata.
- Separate calibration from refinement so calibration results can be audited.
- Include synthetic known-value tests for channel-to-energy and energy-to-d
  conversion paths.
- Record calibration source and timestamp in provenance when data is persisted.

Known limitations: EDXRD support should not be described as production-ready
until calibrated experimental datasets and uncertainty checks are available.

## AI Refinement Guide

Scope: define how AI assistance may interact with scientific calculations.

AI components must recommend or orchestrate deterministic tools; they must not
invent numerical results, hide failed checks, or replace reference calculations.
AI actions should be logged with inputs, selected tool, output summary, warnings,
and any user override.

AI workflow checklist:

- Put tool-boundary primitives under `../src/rietveld_next/ai/`.
- Keep numerical calculations in deterministic packages and call them through
  explicit APIs.
- Store prompts, model names where relevant, seeds, tool inputs, and tool
  outputs when they affect a refinement decision.
- Surface uncertainty, underconstraint, and validation gaps in user-facing
  recommendations.

Known limitations: AI guidance is advisory unless a deterministic calculation
or validated workflow result backs the recommendation.

## HPC Deployment Guide

Scope: describe scheduler-facing expectations for high-throughput refinement.

HPC code should submit reproducible jobs, not hide scheduler-specific behavior.
Each job should declare inputs, environment, resource requests, seed policy,
outputs, and restart behavior.

Implementation checklist:

- Put scheduler abstractions under `../src/rietveld_next/hpc/`.
- Keep facility-specific templates configurable and documented.
- Make job outputs machine-readable and attach provenance.
- Distinguish compile/setup time, queue time, warmup time, and steady-state
  runtime in reports.
- Keep expensive HPC tests opt-in.

Known limitations: local tests can validate job-spec construction and parsing,
but they cannot prove behavior on every cluster scheduler.

## Plugin Developer Guide

Scope: define plugin boundary expectations.

Plugins should extend declared capabilities without bypassing core schemas,
provenance, validation, or package boundaries. Capability metadata should state
inputs, outputs, required dependencies, optional dependencies, deterministic
behavior, and validation status.

Implementation checklist:

- Keep plugin framework code under the established `src/` package boundary.
- Register capabilities through the project capability model rather than hidden
  imports or side effects.
- Validate plugin inputs with typed APIs or schemas.
- Include package-local tests for registration, invalid inputs, and one
  successful path.
- Document any external executable, license, or data dependency.

Known limitations: plugin APIs may evolve; persistent plugin metadata must be
versioned if it becomes part of saved project files.

## Benchmark Guide

Scope: define lightweight, reproducible benchmark practice.

Benchmarks must be opt-in unless explicitly approved for CI. Reports should
separate compile/setup, warmup, and steady-state runtime; include hardware and
dependency metadata; and write machine-readable results where possible.

Benchmark checklist:

- Put benchmark infrastructure under `../src/rietveld_next/benchmarks/`.
- Use deterministic fixtures and fixed seeds.
- Keep smoke benchmarks small enough for local validation.
- Never compare results across machines without reporting environment metadata.
- Document tolerance and statistical method for performance regression checks.

Known limitations: benchmark smoke tests prove harness behavior, not absolute
performance quality.

## Validation Guide

Scope: explain how scientific claims should be validated.

Validation evidence should match the claim. Unit tests, synthetic known-value
tests, regression tests, cross-software comparisons, and experimental reference
datasets answer different questions and should not be conflated.

Validation checklist:

- State the claim being validated.
- Name the fixture, source, units, preprocessing, and expected result.
- Record tolerances and why they are appropriate.
- Store provenance and software versions for external comparisons.
- Mark missing validation explicitly instead of implying completeness.
- Keep large datasets and expensive runs out of default CI unless approved.

Runnable lightweight baseline command:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next/validation -p 'test*.py'
```

Known limitations: the current repository includes lightweight validation
helpers and planning material, but full scientific validation remains feature
and dataset specific.
