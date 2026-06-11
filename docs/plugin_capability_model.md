# Plugin Capability Model

Rietveld Next plugins must declare what they can safely operate on before a
workflow dispatches scientific data to them. The first typed capability model is
`PluginCapability` in `src/rietveld_next/core/architecture/foundation.py`.

## Required Fields

- `name`: stable plugin capability identifier.
- `version`: capability contract version.
- `supported_radiation_types`: one or more radiation identifiers, such as
  `lab_xray_cw`.
- `supported_axes`: one or more axis identifiers, such as `two_theta`.
- `parameter_names`: parameter identifiers exposed by the plugin.
- `units`: parameter-to-unit mapping. Keys must exactly match
  `parameter_names` so every declared parameter has auditable unit metadata and
  no undeclared unit metadata is silently accepted.
- `supports_derivatives`: whether derivative information is available.
- `validation_functions`: stable validation function names.
- `stability`: API stability level.

## Example

```python
from rietveld_next.core.architecture import ApiStability, PluginCapability

capability = PluginCapability(
    name="cw_xrd.profile",
    version="1.0.0",
    supported_radiation_types=("lab_xray_cw", "synchrotron_xray_cw"),
    supported_axes=("two_theta",),
    parameter_names=("u", "v", "w"),
    units={"u": "degree2", "v": "degree2", "w": "degree2"},
    supports_derivatives=True,
    validation_functions=("validate_profile_parameters",),
    stability=ApiStability.PROVISIONAL,
)
```

## Current Limitations

- This model records declared capability metadata only.
- It does not load external plugins or execute plugin code.
- Radiation and axis identifiers are strings until the core data model becomes
  the single shared enum source for plugin contracts.
