# Unit Test Conventions

Unit tests for implementation packages live beside the package under
`src/rietveld_next/<package>/tests/`. This keeps all implementation-adjacent
test code under `src/` and avoids a forbidden top-level `tests/` directory.

Tests should be deterministic, lightweight, and runnable without network
access, GPU hardware, facility data, or large optional benchmarks. Scientific
tests should state the analytical expectation or synthetic fixture they use.

Each new public API should include:

- A primary success-path test.
- At least one invalid-input or edge-case test.
- Explicit checks for units, bounds, or shape where relevant.
- Clear failure assertions that match stable, actionable error text.

Expensive validation and benchmark tests must be opt-in and should not run as
part of the default unit-test command.
