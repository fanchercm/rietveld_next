# M15 Synthetic Pattern Completion Report

Date: 2026-06-12

M15 was completed using the Physics Workstream Batch prompt in
`prompts/28_physics_batch.md`. The milestone scope is limited to deterministic
startup helpers for synthetic pattern generation, phase scale normalization,
and structural validation warnings. These helpers are not claimed as measured
reference validation or production refinement physics.

## Completed Issues

- #99: Reflection tick generation.
- #100: Synthetic pattern generator.
- #101: Standard reference dataset registry.
- #102: Phase scale model.
- #103: Phase fraction calculation.
- #104: Atom occupancy constraints.
- #105: ADP validation checks.

## Implementation Evidence

- `src/rietveld_next/diffraction/models.py` contains the typed public records
  and helpers for M15.
- `src/rietveld_next/diffraction/__init__.py` exports the M15 public API from
  the diffraction package boundary.
- `src/rietveld_next/diffraction/tests/test_models.py` covers known values,
  invalid inputs, structured warnings, deterministic registry order, and
  package-level exports.
- `docs/ground_truths.md` records the current synthetic scope and limitations.

## Scientific Assumptions

- Synthetic peaks use area-normalized Gaussian profiles on a two-theta axis in
  degrees.
- Reflection ticks are deterministic display metadata sorted by two-theta,
  phase identifier, and label.
- Phase fractions use the documented startup proxy:
  `scale * formula_units_per_cell * molecular_mass_g_mol * cell_volume_angstrom3`.
- Occupancy validation reports out-of-range, duplicate, missing-site, and
  linear constraint warnings without silently changing structural parameters.
- ADP validation treats isotropic `U` values in square angstroms and converts
  isotropic `B` values with `B = 8*pi^2*U` before bounds checks.
- Anisotropic ADP checks use principal-minor positive-definiteness tests on the
  symmetric `U` matrix.

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next -p 'test*.py'
```

Additional completion checks:

- `backlog/issues.json`, `backlog/milestones.json`,
  `schemas/project.schema.json`, and `schemas/validation_report.schema.json`
  parse as JSON.
- No forbidden top-level implementation directories are present.

## Limits

- Registry entries are deterministic synthetic placeholders. They are not
  measured standard reference datasets.
- Phase fractions are startup normalization helpers and do not include
  absorption, preferred orientation, microabsorption, or calibrated instrument
  corrections.
- Synthetic pattern values are suitable for API and workflow tests, not for
  scientific claims against external instruments or reference materials.
