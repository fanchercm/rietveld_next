"""Framework-neutral visualization payloads.

The helpers in this module only package already-computed values for display.
They do not evaluate diffraction models, refine parameters, render figures, or
downsample large arrays. Callers that need large-data reduction should perform
that step before constructing these deterministic tuple-backed payloads.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Literal, Mapping, Sequence

from rietveld_next.visualization.series import PlotSeries

AxisRole = Literal["x", "intensity", "residual", "parameter", "phase_fraction", "matrix"]
MatrixKind = Literal["covariance", "correlation"]
ExportFormat = Literal["png", "pdf", "svg", "tiff"]
FigureSizeUnit = Literal["in", "cm", "mm", "px"]
_AXIS_ROLES = {"x", "intensity", "residual", "parameter", "phase_fraction", "matrix"}
_EXPORT_FORMATS = {"png", "pdf", "svg", "tiff"}
_FIGURE_SIZE_UNITS = {"in", "cm", "mm", "px"}
_MATRIX_KINDS = {"covariance", "correlation"}


@dataclass(frozen=True)
class PlotAxis:
    """Axis metadata shared by framework-neutral visualization payloads.

    Args:
        label: Human-readable axis label.
        units: Axis units. Use ``"dimensionless"`` for unitless quantities.
        role: Stable semantic role used by renderers and tests.

    Example:
        >>> PlotAxis("2theta", "deg", "x").label
        '2theta'
    """

    label: str
    units: str
    role: AxisRole

    def __post_init__(self) -> None:
        _require_non_empty("PlotAxis.label", self.label)
        _require_non_empty("PlotAxis.units", self.units)
        if self.role not in _AXIS_ROLES:
            raise ValueError("PlotAxis.role must be a known visualization axis role")


@dataclass(frozen=True)
class ReflectionTick:
    """Reflection tick marker for profile plots.

    Args:
        phase_id: Stable phase identifier.
        position: Already-computed tick position in the profile x-axis units.
        hkl: Miller indices for the reflection.
        label: Optional display label.
    """

    phase_id: str
    position: float
    hkl: tuple[int, int, int]
    label: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty("ReflectionTick.phase_id", self.phase_id)
        object.__setattr__(
            self,
            "position",
            _finite_float("ReflectionTick.position", self.position),
        )
        object.__setattr__(self, "hkl", _hkl_tuple(self.hkl))
        if self.label is not None:
            _require_non_empty("ReflectionTick.label", self.label)


@dataclass(frozen=True)
class ProfilePlotPayload:
    """Observed/calculated/difference profile data with optional phase ticks.

    Args:
        x_axis: Profile x-axis metadata.
        intensity_axis: Observed and calculated intensity axis metadata.
        series: Ordered plot series. Expected labels include values such as
            ``"observed"``, ``"calculated"``, and ``"difference"``.
        residual_axis: Optional residual axis metadata for difference series.
        reflection_ticks: Already-computed reflection tick markers.
        title: Optional display title.
    """

    x_axis: PlotAxis
    intensity_axis: PlotAxis
    series: tuple[PlotSeries, ...]
    residual_axis: PlotAxis | None = None
    reflection_ticks: tuple[ReflectionTick, ...] = ()
    title: str | None = None

    def __post_init__(self) -> None:
        if self.x_axis.role != "x":
            raise ValueError("ProfilePlotPayload.x_axis role must be 'x'")
        if self.intensity_axis.role != "intensity":
            raise ValueError("ProfilePlotPayload.intensity_axis role must be 'intensity'")
        if self.residual_axis is not None and self.residual_axis.role != "residual":
            raise ValueError("ProfilePlotPayload.residual_axis role must be 'residual'")
        series = tuple(self.series)
        if not series:
            raise ValueError("ProfilePlotPayload.series must contain at least one series")
        for item in series:
            if item.x_units != self.x_axis.units:
                raise ValueError("ProfilePlotPayload series x_units must match x_axis units")
            if item.label == "difference" and self.residual_axis is not None:
                if item.y_units != self.residual_axis.units:
                    raise ValueError("difference series y_units must match residual_axis units")
            elif item.y_units != self.intensity_axis.units:
                raise ValueError("profile series y_units must match intensity_axis units")
        object.__setattr__(self, "series", series)
        object.__setattr__(self, "reflection_ticks", tuple(self.reflection_ticks))
        if self.title is not None:
            _require_non_empty("ProfilePlotPayload.title", self.title)


@dataclass(frozen=True)
class BankProfilePayload:
    """One bank's profile payload for multi-bank displays."""

    bank_id: str
    profile: ProfilePlotPayload

    def __post_init__(self) -> None:
        _require_non_empty("BankProfilePayload.bank_id", self.bank_id)


@dataclass(frozen=True)
class MultiBankProfilePayload:
    """Deterministic aggregation of per-bank profile payloads."""

    banks: tuple[BankProfilePayload, ...]
    x_axis: PlotAxis
    intensity_axis: PlotAxis
    title: str | None = None

    def __post_init__(self) -> None:
        banks = tuple(self.banks)
        if not banks:
            raise ValueError("MultiBankProfilePayload.banks must contain at least one bank")
        bank_ids = [bank.bank_id for bank in banks]
        if len(set(bank_ids)) != len(bank_ids):
            raise ValueError("MultiBankProfilePayload bank_id values must be unique")
        for bank in banks:
            if bank.profile.x_axis != self.x_axis:
                raise ValueError("all bank profiles must share the multi-bank x_axis")
            if bank.profile.intensity_axis != self.intensity_axis:
                raise ValueError("all bank profiles must share the multi-bank intensity_axis")
        object.__setattr__(self, "banks", banks)
        if self.title is not None:
            _require_non_empty("MultiBankProfilePayload.title", self.title)


@dataclass(frozen=True)
class ResidualHeatmapPayload:
    """Rectangular residual matrix for heatmap renderers."""

    x_axis: PlotAxis
    residual_axis: PlotAxis
    x: tuple[float, ...]
    row_labels: tuple[str, ...]
    residuals: tuple[tuple[float, ...], ...]
    title: str | None = None

    def __post_init__(self) -> None:
        if self.x_axis.role != "x":
            raise ValueError("ResidualHeatmapPayload.x_axis role must be 'x'")
        if self.residual_axis.role != "residual":
            raise ValueError("ResidualHeatmapPayload.residual_axis role must be 'residual'")
        x = _as_float_tuple("ResidualHeatmapPayload.x", self.x)
        row_labels = _string_tuple("ResidualHeatmapPayload.row_labels", self.row_labels)
        residuals = _matrix_tuple(
            "ResidualHeatmapPayload.residuals",
            self.residuals,
            row_count=len(row_labels),
            column_count=len(x),
        )
        object.__setattr__(self, "x", x)
        object.__setattr__(self, "row_labels", row_labels)
        object.__setattr__(self, "residuals", residuals)
        if self.title is not None:
            _require_non_empty("ResidualHeatmapPayload.title", self.title)


@dataclass(frozen=True)
class EvolutionSeries:
    """One already-computed series for an evolution chart."""

    label: str
    values: tuple[float, ...]
    units: str

    def __post_init__(self) -> None:
        _require_non_empty("EvolutionSeries.label", self.label)
        _require_non_empty("EvolutionSeries.units", self.units)
        object.__setattr__(self, "values", _as_float_tuple("EvolutionSeries.values", self.values))


@dataclass(frozen=True)
class EvolutionChartPayload:
    """Sequential parameter or phase-fraction chart data."""

    x_axis: PlotAxis
    y_axis: PlotAxis
    x: tuple[float, ...]
    series: tuple[EvolutionSeries, ...]
    title: str | None = None

    def __post_init__(self) -> None:
        x = _as_float_tuple("EvolutionChartPayload.x", self.x)
        series = tuple(self.series)
        if not series:
            raise ValueError("EvolutionChartPayload.series must contain at least one series")
        for item in series:
            if len(item.values) != len(x):
                raise ValueError("EvolutionChartPayload series lengths must match x length")
            if item.units != self.y_axis.units:
                raise ValueError("EvolutionChartPayload series units must match y_axis units")
        object.__setattr__(self, "x", x)
        object.__setattr__(self, "series", series)
        if self.title is not None:
            _require_non_empty("EvolutionChartPayload.title", self.title)


@dataclass(frozen=True)
class MatrixPayload:
    """Labeled covariance or correlation matrix payload."""

    kind: MatrixKind
    labels: tuple[str, ...]
    units: tuple[str, ...]
    values: tuple[tuple[float, ...], ...]
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in _MATRIX_KINDS:
            raise ValueError("MatrixPayload.kind must be covariance or correlation")
        labels = _string_tuple("MatrixPayload.labels", self.labels)
        units = _string_tuple("MatrixPayload.units", self.units)
        if len(labels) != len(units):
            raise ValueError("MatrixPayload.labels and units lengths must match")
        values = _matrix_tuple(
            "MatrixPayload.values",
            self.values,
            row_count=len(labels),
            column_count=len(labels),
        )
        warnings = tuple(self.warnings)
        for index, warning in enumerate(warnings):
            _require_non_empty(f"MatrixPayload.warnings[{index}]", warning)
        object.__setattr__(self, "labels", labels)
        object.__setattr__(self, "units", units)
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "warnings", warnings)


@dataclass(frozen=True)
class DependencyNode:
    """Node in a parameter dependency graph."""

    node_id: str
    label: str
    kind: str

    def __post_init__(self) -> None:
        _require_non_empty("DependencyNode.node_id", self.node_id)
        _require_non_empty("DependencyNode.label", self.label)
        _require_non_empty("DependencyNode.kind", self.kind)


@dataclass(frozen=True)
class DependencyEdge:
    """Directed edge in a parameter dependency graph."""

    source_id: str
    target_id: str
    relationship: str

    def __post_init__(self) -> None:
        _require_non_empty("DependencyEdge.source_id", self.source_id)
        _require_non_empty("DependencyEdge.target_id", self.target_id)
        _require_non_empty("DependencyEdge.relationship", self.relationship)


@dataclass(frozen=True)
class DependencyGraphPayload:
    """Framework-neutral dependency graph payload."""

    nodes: tuple[DependencyNode, ...]
    edges: tuple[DependencyEdge, ...]

    def __post_init__(self) -> None:
        nodes = tuple(self.nodes)
        if not nodes:
            raise ValueError("DependencyGraphPayload.nodes must contain at least one node")
        node_ids = [node.node_id for node in nodes]
        if len(set(node_ids)) != len(node_ids):
            raise ValueError("DependencyGraphPayload node_id values must be unique")
        valid_ids = set(node_ids)
        edges = tuple(self.edges)
        for edge in edges:
            if edge.source_id not in valid_ids or edge.target_id not in valid_ids:
                raise ValueError("DependencyGraphPayload edges must reference existing node ids")
        object.__setattr__(self, "nodes", nodes)
        object.__setattr__(self, "edges", edges)


@dataclass(frozen=True)
class ReflectionRow:
    """One row in a reflection browser payload."""

    phase_id: str
    hkl: tuple[int, int, int]
    position: float
    position_units: str
    bank_id: str | None = None
    d_spacing: float | None = None
    intensity: float | None = None

    def __post_init__(self) -> None:
        _require_non_empty("ReflectionRow.phase_id", self.phase_id)
        object.__setattr__(self, "hkl", _hkl_tuple(self.hkl))
        object.__setattr__(
            self,
            "position",
            _finite_float("ReflectionRow.position", self.position),
        )
        _require_non_empty("ReflectionRow.position_units", self.position_units)
        if self.bank_id is not None:
            _require_non_empty("ReflectionRow.bank_id", self.bank_id)
        if self.d_spacing is not None:
            spacing = _finite_float("ReflectionRow.d_spacing", self.d_spacing)
            if spacing <= 0.0:
                raise ValueError("ReflectionRow.d_spacing must be positive")
            object.__setattr__(self, "d_spacing", spacing)
        if self.intensity is not None:
            object.__setattr__(
                self,
                "intensity",
                _finite_float("ReflectionRow.intensity", self.intensity),
            )


@dataclass(frozen=True)
class ReflectionBrowserPayload:
    """Typed table payload for reflection browsing and filtering."""

    rows: tuple[ReflectionRow, ...]
    sort_key: str = "position"
    selected_phase_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        rows = tuple(self.rows)
        if not rows:
            raise ValueError("ReflectionBrowserPayload.rows must contain at least one row")
        if self.sort_key not in {"position", "phase_id", "bank_id"}:
            raise ValueError(
                "ReflectionBrowserPayload.sort_key must be position, phase_id, or bank_id"
            )
        selected_phase_ids = tuple(self.selected_phase_ids)
        for index, phase_id in enumerate(selected_phase_ids):
            _require_non_empty(f"ReflectionBrowserPayload.selected_phase_ids[{index}]", phase_id)
        object.__setattr__(self, "rows", rows)
        object.__setattr__(self, "selected_phase_ids", selected_phase_ids)


@dataclass(frozen=True)
class ExclusionRange:
    """Closed x-axis range for mask/exclusion editing."""

    start: float
    end: float
    reason: str

    def __post_init__(self) -> None:
        start = _finite_float("ExclusionRange.start", self.start)
        end = _finite_float("ExclusionRange.end", self.end)
        if start > end:
            raise ValueError("ExclusionRange.start must be less than or equal to end")
        _require_non_empty("ExclusionRange.reason", self.reason)
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)


@dataclass(frozen=True)
class MaskExclusionEditorPayload:
    """Scriptable mask/exclusion editor payload."""

    x_axis: PlotAxis
    ranges: tuple[ExclusionRange, ...]
    editable: bool = True
    selected_range_index: int | None = None

    def __post_init__(self) -> None:
        if self.x_axis.role != "x":
            raise ValueError("MaskExclusionEditorPayload.x_axis role must be 'x'")
        ranges = tuple(self.ranges)
        object.__setattr__(self, "ranges", ranges)
        if self.selected_range_index is not None:
            if self.selected_range_index < 0 or self.selected_range_index >= len(ranges):
                raise ValueError(
                    "MaskExclusionEditorPayload.selected_range_index is out of range"
                )


@dataclass(frozen=True)
class PublicationFigureExportRequest:
    """Validated request model for publication figure export.

    This model describes export intent only. It does not render, rasterize, or
    write output files.
    """

    figure_id: str
    format: ExportFormat
    width: float
    height: float
    size_units: FigureSizeUnit
    dpi: int | None = None
    transparent_background: bool = False
    include_provenance: bool = True
    metadata: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        _require_non_empty("PublicationFigureExportRequest.figure_id", self.figure_id)
        if self.format not in _EXPORT_FORMATS:
            raise ValueError("PublicationFigureExportRequest.format must be png, pdf, svg, or tiff")
        width = _finite_float("PublicationFigureExportRequest.width", self.width)
        height = _finite_float("PublicationFigureExportRequest.height", self.height)
        if width <= 0.0 or height <= 0.0:
            raise ValueError("PublicationFigureExportRequest width and height must be positive")
        if self.size_units not in _FIGURE_SIZE_UNITS:
            raise ValueError(
                "PublicationFigureExportRequest.size_units must be in, cm, mm, or px"
            )
        if self.dpi is not None and self.dpi <= 0:
            raise ValueError("PublicationFigureExportRequest.dpi must be positive when provided")
        metadata = dict(self.metadata or {})
        for key, value in metadata.items():
            _require_non_empty("PublicationFigureExportRequest.metadata key", key)
            _require_non_empty(f"PublicationFigureExportRequest.metadata[{key!r}]", value)
        object.__setattr__(self, "width", width)
        object.__setattr__(self, "height", height)
        object.__setattr__(self, "metadata", MappingProxyType(metadata))


def profile_plot_payload(
    x: Sequence[float],
    observed: Sequence[float],
    *,
    x_label: str,
    x_units: str,
    intensity_units: str,
    calculated: Sequence[float] | None = None,
    difference: Sequence[float] | None = None,
    reflection_ticks: Sequence[ReflectionTick] = (),
    title: str | None = None,
) -> ProfilePlotPayload:
    """Build a profile plot payload from already-computed display arrays."""

    x_values = _as_float_tuple("x", x)
    series = [
        PlotSeries(
            "observed",
            x_values,
            _as_float_tuple("observed", observed),
            x_units,
            intensity_units,
        )
    ]
    if calculated is not None:
        series.append(
            PlotSeries(
                "calculated",
                x_values,
                _as_float_tuple("calculated", calculated),
                x_units,
                intensity_units,
            )
        )
    residual_axis = None
    if difference is not None:
        residual_axis = PlotAxis("observed - calculated", intensity_units, "residual")
        series.append(
            PlotSeries(
                "difference",
                x_values,
                _as_float_tuple("difference", difference),
                x_units,
                intensity_units,
            )
        )
    return ProfilePlotPayload(
        x_axis=PlotAxis(x_label, x_units, "x"),
        intensity_axis=PlotAxis("intensity", intensity_units, "intensity"),
        residual_axis=residual_axis,
        series=tuple(series),
        reflection_ticks=tuple(reflection_ticks),
        title=title,
    )


def multi_bank_profile_payload(
    banks: Sequence[BankProfilePayload],
    *,
    title: str | None = None,
) -> MultiBankProfilePayload:
    """Aggregate per-bank profile payloads without resampling or alignment."""

    bank_tuple = tuple(banks)
    if not bank_tuple:
        raise ValueError("banks must contain at least one bank")
    return MultiBankProfilePayload(
        banks=bank_tuple,
        x_axis=bank_tuple[0].profile.x_axis,
        intensity_axis=bank_tuple[0].profile.intensity_axis,
        title=title,
    )


def residual_heatmap_payload(
    x: Sequence[float],
    residuals: Sequence[Sequence[float]],
    *,
    row_labels: Sequence[str],
    x_label: str,
    x_units: str,
    residual_units: str,
    title: str | None = None,
) -> ResidualHeatmapPayload:
    """Build a rectangular residual heatmap payload."""

    return ResidualHeatmapPayload(
        x_axis=PlotAxis(x_label, x_units, "x"),
        residual_axis=PlotAxis("residual", residual_units, "residual"),
        x=tuple(x),
        row_labels=tuple(row_labels),
        residuals=tuple(tuple(row) for row in residuals),
        title=title,
    )


def parameter_evolution_payload(
    steps: Sequence[float],
    values_by_parameter: Mapping[str, Sequence[float]],
    *,
    step_units: str = "index",
    value_units: str = "parameter units",
    title: str | None = None,
) -> EvolutionChartPayload:
    """Build parameter evolution chart data from sequential results."""

    series = tuple(
        EvolutionSeries(label, tuple(values), value_units)
        for label, values in values_by_parameter.items()
    )
    return EvolutionChartPayload(
        x_axis=PlotAxis("step", step_units, "x"),
        y_axis=PlotAxis("parameter value", value_units, "parameter"),
        x=tuple(steps),
        series=series,
        title=title,
    )


def phase_fraction_evolution_payload(
    steps: Sequence[float],
    fractions_by_phase: Mapping[str, Sequence[float]],
    *,
    step_units: str = "index",
    fraction_units: str = "fraction",
    title: str | None = None,
) -> EvolutionChartPayload:
    """Build phase-fraction evolution chart data from sequential results."""

    series = tuple(
        EvolutionSeries(label, tuple(values), fraction_units)
        for label, values in fractions_by_phase.items()
    )
    return EvolutionChartPayload(
        x_axis=PlotAxis("step", step_units, "x"),
        y_axis=PlotAxis("phase fraction", fraction_units, "phase_fraction"),
        x=tuple(steps),
        series=series,
        title=title,
    )


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


def _finite_float(name: str, value: float) -> float:
    converted = float(value)
    if not math.isfinite(converted):
        raise ValueError(f"{name} must be finite")
    return converted


def _as_float_tuple(name: str, values: Sequence[float]) -> tuple[float, ...]:
    converted = tuple(
        _finite_float(f"{name}[{index}]", value)
        for index, value in enumerate(values)
    )
    if not converted:
        raise ValueError(f"{name} must contain at least one value")
    return converted


def _string_tuple(name: str, values: Sequence[str]) -> tuple[str, ...]:
    converted = tuple(values)
    if not converted:
        raise ValueError(f"{name} must contain at least one value")
    for index, value in enumerate(converted):
        _require_non_empty(f"{name}[{index}]", value)
    return converted


def _matrix_tuple(
    name: str,
    values: Sequence[Sequence[float]],
    *,
    row_count: int,
    column_count: int,
) -> tuple[tuple[float, ...], ...]:
    matrix = tuple(
        tuple(
            _finite_float(f"{name}[{row}][{column}]", value)
            for column, value in enumerate(row_values)
        )
        for row, row_values in enumerate(values)
    )
    if len(matrix) != row_count:
        raise ValueError(f"{name} row count must be {row_count}, got {len(matrix)}")
    for row_index, row in enumerate(matrix):
        if len(row) != column_count:
            raise ValueError(f"{name} row {row_index} length must be {column_count}, got {len(row)}")
    return matrix


def _hkl_tuple(values: Sequence[int]) -> tuple[int, int, int]:
    converted = tuple(values)
    if len(converted) != 3:
        raise ValueError("hkl must contain exactly three indices")
    if not all(isinstance(value, int) for value in converted):
        raise TypeError("hkl indices must be integers")
    return (converted[0], converted[1], converted[2])
