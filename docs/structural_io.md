# Structural IO

M12 provides a small, dependency-free structural IO baseline for issues #86-#89.
It is intended for deterministic startup plumbing and tests, not complete
crystallographic validation.

## Public API

Location: `src/rietveld_next/structure/`

```python
UnitCell(a, b, c, alpha, beta, gamma)
AtomSite(label, type_symbol, fract_x, fract_y, fract_z, occupancy=None)
CrystalStructure(...)
validate_cif_text(cif_text)
import_cif_v0(cif_text)
lookup_space_group(identifier)
generate_reflections(cell, space_group, max_index=1)
```

## Scope

- CIF import v0 reads scalar cell tags, supported space-group fields, and simple
  atom-site loops.
- CIF validation reports missing cell fields, missing/ambiguous startup
  space-group data, missing atom-site loops, and unsupported numeric values.
- The space-group lookup registry includes P1 and Fd-3m metadata. Only P1 has
  operation support in this increment.
- Reflection generation enumerates P1 Miller indices up to an explicit
  `max_index` and computes d-spacings from the validated unit cell.

## Limitations

This increment does not parse the full CIF/STAR grammar, expand symmetry
operations for non-P1 groups, apply systematic absences, or claim agreement with
external crystallographic programs. Those checks remain later validation work.
