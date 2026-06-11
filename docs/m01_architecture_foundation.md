# M01 Architecture Foundation

This document covers the lightweight architecture foundation helpers in
`src/rietveld_next/core/architecture/`. These helpers are metadata and workflow
utilities only; they do not perform scientific calculations.

## Covered Issues

This increment provides implementation coverage for:

- #4 shared architecture error taxonomy
- #7 JSON configuration loading
- #8 provenance event envelope
- #9 environment capture
- #11 public API stability levels
- #12 feature flag registry
- #15 release artifact manifest

It builds on the existing boundary checks for #1, #3, #13, and #14.

## Public API

Import the helpers from `rietveld_next.core.architecture`:

```python
from pathlib import Path

from rietveld_next.core.architecture import (
    FeatureFlag,
    FeatureFlagRegistry,
    build_release_manifest,
    capture_environment,
    create_provenance_event,
    load_configuration,
)

config = load_configuration(
    [Path("local.json")],
    defaults={"schema_version": "1.0.0"},
    overrides={"feature": {"enabled": True}},
)

event = create_provenance_event(
    actor="codex",
    action="m01.foundation.updated",
    timestamp_utc="2026-06-11T12:00:00Z",
    subject="src/rietveld_next/core/architecture/foundation.py",
)

registry = FeatureFlagRegistry(
    (
        FeatureFlag(
            name="profile.kernel.v2",
            description="Enable the second profile-kernel interface.",
        ),
    )
)

snapshot = capture_environment(["RIETVELD_NEXT_PROFILE"])
manifest = build_release_manifest(
    root=Path("."),
    artifact_paths=[Path("README.md")],
    version="0.1.0",
    created_at_utc="2026-06-11T12:00:00Z",
)
```

## Validation And Determinism

- Configuration files must be JSON objects and are merged deterministically.
- Feature flag names must be stable identifiers and unique within a registry.
- Provenance events use explicit UTC timestamps. If no event ID is supplied, a
  stable ID is derived from canonical event fields.
- Environment capture records Python/platform metadata and only explicitly
  requested environment variables.
- Release manifests hash existing files and store relative paths, byte counts,
  and lowercase SHA-256 digests.

## Limitations

- Configuration loading supports JSON only.
- Environment capture intentionally avoids dumping the full environment.
- Release manifest helpers do not publish or package artifacts.
- Plugin capability modeling and ADR workflow templates remain separate M01
  follow-up work.

## Test Command

```bash
PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next/core/architecture
```
