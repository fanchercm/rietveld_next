# Batch D Foundation

Batch D adds small, dependency-free starter APIs for specialized physics,
storage, and validation. These APIs are reference implementations and schema
anchors, not final scientific validation against facility or cross-software
datasets.

## Covered Issues

- Issue #126: TOF histogram axes use strictly increasing positive bin edges in
  microseconds and can carry a detector-bank identifier for multi-bank data.
- Issue #153: EDXRD histogram axes use strictly increasing positive bin edges in
  keV and support a linear channel-to-energy edge calibration.
- Issue #141: Magnetic moments store three components in Bohr magnetons with an
  explicit coordinate frame.
- Issue #36: Directory-backed project packages can be read from `project.json`
  with optional `manifest.json`; the reader is read-only and fails clearly on
  missing or corrupt metadata.
- Issue #248: Unit tests remain package-local under `src/rietveld_next/**/tests`
  until repository build conventions permit a different layout.

## Validation Policy

The Batch D tests are deterministic unit and serialization checks. Scientific
validation is limited to analytical geometry expectations such as bin centers,
bin widths, and vector magnitudes. Facility data, cross-software comparisons,
and expensive benchmarks remain follow-up work and must stay opt-in.

## Usage Examples

```python
from rietveld_next.tof import TimeOfFlightHistogramAxis
from rietveld_next.edxrd import EnergyHistogramAxis
from rietveld_next.neutron.magnetic import MagneticMoment
from rietveld_next.storage import read_project_package

tof_axis = TimeOfFlightHistogramAxis((1000.0, 1010.0, 1030.0), bank_id="bankA")
energy_axis = EnergyHistogramAxis.from_linear_calibration(
    channel_count=3,
    offset_keV=5.0,
    gain_keV_per_channel=0.5,
    channel_start=2,
)
moment = MagneticMoment("mn1", (0.0, 0.0, 3.2))
package = read_project_package("example.rnx")
```
