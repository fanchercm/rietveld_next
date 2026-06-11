# M01 Completion Report

Milestone: M01 Src-first architecture foundation

Status: Complete for the foundation increment represented by issues #1-15.

## Validation Summary

The M01 implementation is lightweight, deterministic, and CI-suitable. It does
not introduce large benchmarks, GPU requirements, facility-only resources, or
scientific formula changes.

Validation commands:

```bash
git diff --check
PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next/core/architecture
PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next/core
python3 -B -m unittest discover -s src
python3 -m json.tool schemas/project.schema.json
```

Source-layout guard:

```bash
find . -maxdepth 1 -type d \( -name core -o -name diffraction -o -name xray -o -name neutron -o -name tof -o -name edxrd -o -name optimization -o -name workflows -o -name ai -o -name hpc -o -name desktop -o -name web -o -name benchmarks -o -name tests \) -print
```

Expected output is empty.

## Issue Closure Evidence

| Issue | Closure evidence |
| --- | --- |
| #1 Initialize src-first monorepo layout | `docs/PACKAGE_TREE.md`, `architecture/src_layout_guardrails.md`, and `check_repository_boundaries()` enforce `src/` as the implementation root and reject forbidden top-level source/test directories. |
| #2 Define workspace build conventions | `docs/workspace_build_conventions.md` documents source path, unittest commands, boundary checks, benchmark policy, and current packaging limitations. |
| #3 Create package boundary document | `architecture/repository_boundaries.md` defines source, dependency, public API, plugin, and Codex placement boundaries. |
| #4 Implement shared error taxonomy | `ArchitectureErrorCode` and `ArchitectureError` in `src/rietveld_next/core/architecture/foundation.py` provide stable, structured architecture-foundation errors with tests. |
| #5 Define plugin capability model | `PluginCapability` defines radiation, axis, parameter, unit, derivative, validation, and stability metadata; tests require unit keys to match parameter names. |
| #6 Create schema versioning policy | `docs/schema_serialization.md`, `schemas/project.schema.json`, and schema validation tests establish the `1.0.x` compatibility line and reject invalid versions. |
| #7 Implement configuration loading system | `load_configuration()` merges JSON defaults, files, and overrides deterministically with structured errors and tests. |
| #8 Define provenance event envelope | `ProvenanceEvent` and `create_provenance_event()` define immutable event envelopes with deterministic IDs and tests for mutation resistance. |
| #9 Implement environment capture module | `EnvironmentSnapshot` and `capture_environment()` record Python/platform metadata plus explicitly requested environment variables with tests. |
| #10 Create architecture decision record workflow | `docs/adr_workflow.md` and `architecture/0000-adr-template.md` define ADR status values, required sections, review rules, validation expectations, and provenance. |
| #11 Define public API stability levels | `ApiStability` defines internal, experimental, provisional, stable, and deprecated levels and is used by feature flags and plugin capabilities. |
| #12 Implement feature flag registry | `FeatureFlag` and `FeatureFlagRegistry` define typed flags, uniqueness checks, deterministic serialization, and override validation. |
| #13 Create source layout linter | `check_repository_boundaries()` reports forbidden top-level directories, stale package-tree location, missing source root, and unknown top-level directories; tests cover success and failure cases. |
| #14 Define dependency boundary checks | `DISALLOWED_IMPORT_PREFIXES` and import parsing in `boundaries.py` enforce initial Python dependency direction for core, diffraction, and optimization packages, including direct and relative import forms. |
| #15 Create release artifact manifest | `ReleaseArtifact`, `ReleaseManifest`, and `build_release_manifest()` hash existing files, validate relative paths, require unique artifacts, and serialize deterministically. |

## Known Follow-Up Work

These are not blockers for closing M01 foundation issues:

- Add language-specific boundary checks when Rust, TypeScript, or other package
  trees are introduced.
- Add a packaging file such as `pyproject.toml` when packaging scope is
  assigned.
- Add an ADR CLI or automation if ADR creation becomes frequent.
- Implement plugin discovery/loading separately from the capability metadata
  model.
- Extend release manifest use into packaging and release workflows when release
  automation is assigned.
