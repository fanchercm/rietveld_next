# Architecture Boundary Report

## Scope

This report records the Batch A architecture-boundary assessment for the current
repository layout. The executable checks live in
`src/rietveld_next/core/architecture/`.

## Current Result

- No forbidden top-level implementation directories are present.
- The canonical package-tree document is `docs/PACKAGE_TREE.md`.
- The stale root-level `PACKAGE_TREE.md` path has been removed.
- `backend_corpus/` is treated as validation support content, not
  implementation source.
- Package-local tests live under `src/rietveld_next/.../tests/`.
- Core, diffraction, and optimization packages are checked for disallowed
  imports from AI, UI, workflow, or HPC packages according to their boundary
  rules.

## Validation Commands

```bash
PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next/core/architecture
PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next/core
python3 -B -m unittest discover -s src
python3 -m json.tool schemas/project.schema.json
```

## Limitations

- The checker is intentionally lightweight and covers Python imports only.
- Future Rust, TypeScript, or workflow packages should add language-specific
  boundary checks under `src/` when those package trees are introduced.
- Unknown top-level directories are reported so new support directories are
  documented before use.
