# Workspace Build Conventions

The current repository is a `src/`-first Python workspace with package-local
tests. There is no top-level implementation package and no committed packaging
tool configuration yet.

## Source Path

Use `PYTHONPATH=src` for package-local commands that start below
`src/rietveld_next/`:

```bash
PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next/core/architecture
PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next/core
```

Full source discovery from the repository root can be run with:

```bash
python3 -B -m unittest discover -s src
```

## Lint And Boundary Checks

The current lightweight architecture lint is the boundary checker exercised by:

```bash
PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next/core/architecture
```

This command verifies forbidden top-level implementation directories, stale
`PACKAGE_TREE.md` placement, and Python import boundaries.

## Benchmarks

Benchmarks must be opt-in and must not run as part of the default unit-test
commands. Benchmark commands should report warmup and steady-state timing when
benchmark infrastructure is introduced.

## Limitations

- A packaging file such as `pyproject.toml` is not yet committed.
- A dedicated formatter or static type-check command is not yet committed.
- Future build-tool additions must update this document and the boundary tests.
