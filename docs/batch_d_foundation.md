# Batch D Foundation

Batch D adds small, dependency-free starter APIs for specialized physics,
storage, and validation. These APIs are reference implementations and schema
anchors, not final scientific validation against facility or cross-software
datasets.

## Covered Issues

- Issue #126: TOF histogram axes use strictly increasing positive bin edges in
  microseconds and can carry a detector-bank identifier for multi-bank data.
- Issue #127: TOF detector-bank entities record a stable bank identifier,
  representative two-theta angle in degrees, detector count, optional
  sample-to-detector distance in meters, and optional linked TOF calibration.
- Issue #128: TOF calibration parameter sets record DIFC/DIFA/zero values with
  explicit microsecond and angstrom units plus optional d-spacing validity
  bounds and provenance.
- Issue #153: EDXRD histogram axes use strictly increasing positive bin edges in
  keV and support a linear channel-to-energy edge calibration.
- Issue #154: EDXRD channel-to-energy calibration supports deterministic
  polynomial edge evaluation with coefficients ordered by ascending channel
  power and units of `keV / channel**i`.
- Issue #155: EDXRD fixed-angle Bragg helpers convert between photon energy in
  keV and d-spacing in angstroms using a fixed two-theta angle in degrees.
- Issue #141: Magnetic moments store three components in Bohr magnetons with an
  explicit coordinate frame.
- Issue #142: Magnetic propagation vectors store three reciprocal-lattice
  fractional components in reciprocal lattice units and expose phase helpers for
  direct-lattice fractional positions.
- Issue #149: Magnetic moment payloads can validate declared magnitudes against
  the Euclidean component norm, and moments expose explicit Bohr-magneton
  magnitude bound validation.
- Issue #36: Directory-backed project packages can be read from `project.json`
  with optional `manifest.json`; the reader is read-only and fails clearly on
  missing or corrupt metadata.
- Issue #37: Directory-backed project packages can be written with
  deterministic JSON and explicit overwrite protection.
- Issue #38: Project JSON files can be validated through the dependency-free
  storage CLI helper.
- Issue #39: NeXus external dataset references record package URI, internal
  dataset path, shape, dtype, and units without embedding large arrays.
- Issue #40: HDF5 metadata references use the same external-reference record
  with `format="hdf5"`.
- Issue #41: Zarr profile-array references use package-relative array URIs and
  internal dataset paths without importing optional Zarr dependencies.
- Issue #42: Result tables can be written as deterministic JSON-lines
  placeholders at Parquet workflow paths until an optional Parquet dependency is
  introduced.
- Issue #43: Refinement parameters can be exported as deterministic JSON-lines
  placeholders at Arrow workflow paths.
- Issue #45: Project package integrity can be checked without mutating files.
- Issue #44: Provenance events can be appended to deterministic JSONL logs.
- Issue #46: Package-relative and local file data URIs can be resolved with
  package escape checks.
- Issue #47: Package files can be listed with size and SHA-256 checksums and
  verified against a manifest.
- Issue #48: Import warning reports use deterministic JSON with stable warning
  codes for non-blocking import findings.
- Issue #49: Project package metadata can be written as deterministic
  `project.json.gz` when gzip compression is explicitly selected.
- Issue #50: Storage regression tests cover package write/read, gzip metadata,
  warning reports, URI resolution, manifests, CLI validation, and adapter
  placeholder exports.
- Issue #248: Unit tests remain package-local under `src/rietveld_next/**/tests`
  until repository build conventions permit a different layout.

## Validation Policy

The Batch D tests are deterministic unit and serialization checks. Scientific
validation is limited to analytical geometry expectations such as bin centers,
bin widths, vector magnitudes, and reciprocal-space phase dot products. Facility
data, cross-software comparisons, and expensive benchmarks remain follow-up work
and must stay opt-in.

## Usage Examples

```python
from rietveld_next.tof import (
    TimeOfFlightCalibrationParameters,
    TimeOfFlightDetectorBank,
    TimeOfFlightHistogramAxis,
)
from rietveld_next.edxrd import (
    EnergyHistogramAxis,
    fixed_angle_bragg_d_spacing_angstrom,
    fixed_angle_bragg_energy_keV,
)
from rietveld_next.neutron.magnetic import MagneticMoment, PropagationVector
from rietveld_next.storage import read_project_package, write_project_package

tof_axis = TimeOfFlightHistogramAxis((1000.0, 1010.0, 1030.0), bank_id="bankA")
tof_calibration = TimeOfFlightCalibrationParameters(
    18000.0,
    zero_microseconds=2.5,
    bank_id="bankA",
)
tof_bank = TimeOfFlightDetectorBank(
    "bankA",
    two_theta_degrees=145.0,
    detector_count=128,
    calibration=tof_calibration,
)
energy_axis = EnergyHistogramAxis.from_linear_calibration(
    channel_count=3,
    offset_keV=5.0,
    gain_keV_per_channel=0.5,
    channel_start=2,
)
curved_energy_axis = EnergyHistogramAxis.from_polynomial_calibration(
    channel_count=3,
    coefficients_keV_by_channel_power=(5.0, 0.5, 0.25),
    channel_start=2,
)
energy_keV = fixed_angle_bragg_energy_keV(
    d_spacing_angstrom=1.0,
    two_theta_degrees=60.0,
)
d_spacing_angstrom = fixed_angle_bragg_d_spacing_angstrom(
    energy_keV=energy_keV,
    two_theta_degrees=60.0,
)
moment = MagneticMoment("mn1", (0.0, 0.0, 3.2))
moment.validate_magnitude(max_bohr_magneton=5.0)
k_vector = PropagationVector("k1", (0.5, 0.0, 0.0))
phase_turns = k_vector.phase_turns((1.0, 0.0, 0.0))
package = read_project_package("example.rnx")
written = write_project_package(
    "new-example.rnx",
    package.project,
    manifest={"format_version": "1.0.0"},
)
```
