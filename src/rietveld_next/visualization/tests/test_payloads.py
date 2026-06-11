"""Tests for framework-neutral visualization payloads."""

from __future__ import annotations

import unittest

from rietveld_next.visualization import (
    BankProfilePayload,
    DependencyEdge,
    DependencyGraphPayload,
    DependencyNode,
    ExclusionRange,
    MaskExclusionEditorPayload,
    MatrixPayload,
    PlotAxis,
    PublicationFigureExportRequest,
    ReflectionBrowserPayload,
    ReflectionRow,
    ReflectionTick,
    multi_bank_profile_payload,
    parameter_evolution_payload,
    phase_fraction_evolution_payload,
    profile_plot_payload,
    residual_heatmap_payload,
)


class VisualizationPayloadTests(unittest.TestCase):
    """Validate typed visualization payload construction."""

    def test_profile_plot_payload_includes_difference_and_ticks(self) -> None:
        payload = profile_plot_payload(
            [10.0, 20.0],
            [100.0, 120.0],
            calculated=[98.0, 119.0],
            difference=[2.0, 1.0],
            x_label="2theta",
            x_units="deg",
            intensity_units="counts",
            reflection_ticks=(ReflectionTick("phase-a", 10.1, (1, 0, 0)),),
        )

        self.assertEqual([series.label for series in payload.series], ["observed", "calculated", "difference"])
        self.assertEqual(payload.x_axis.label, "2theta")
        self.assertEqual(payload.residual_axis.label, "observed - calculated")
        self.assertEqual(payload.reflection_ticks[0].hkl, (1, 0, 0))

    def test_profile_plot_payload_rejects_length_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "lengths must match"):
            profile_plot_payload(
                [10.0, 20.0],
                [100.0],
                x_label="2theta",
                x_units="deg",
                intensity_units="counts",
            )

    def test_multi_bank_profile_payload_preserves_order_and_requires_unique_banks(self) -> None:
        first = BankProfilePayload(
            "bank-1",
            profile_plot_payload(
                [1.0],
                [10.0],
                x_label="tof",
                x_units="us",
                intensity_units="counts",
            ),
        )
        second = BankProfilePayload(
            "bank-2",
            profile_plot_payload(
                [2.0],
                [20.0],
                x_label="tof",
                x_units="us",
                intensity_units="counts",
            ),
        )

        payload = multi_bank_profile_payload((first, second), title="banks")

        self.assertEqual([bank.bank_id for bank in payload.banks], ["bank-1", "bank-2"])
        with self.assertRaisesRegex(ValueError, "unique"):
            multi_bank_profile_payload((first, first))

    def test_residual_heatmap_payload_requires_rectangular_residuals(self) -> None:
        payload = residual_heatmap_payload(
            [1.0, 2.0],
            [[0.1, -0.1], [0.2, -0.2]],
            row_labels=["bank-1", "bank-2"],
            x_label="2theta",
            x_units="deg",
            residual_units="sigma",
        )

        self.assertEqual(payload.residuals[1], (0.2, -0.2))
        with self.assertRaisesRegex(ValueError, "row 0 length"):
            residual_heatmap_payload(
                [1.0, 2.0],
                [[0.1]],
                row_labels=["bank-1"],
                x_label="2theta",
                x_units="deg",
                residual_units="sigma",
            )

    def test_parameter_and_phase_evolution_payloads_validate_lengths(self) -> None:
        parameter_payload = parameter_evolution_payload(
            [0.0, 1.0],
            {"scale": [1.0, 1.1]},
            value_units="dimensionless",
        )
        phase_payload = phase_fraction_evolution_payload(
            [0.0, 1.0],
            {"alpha": [0.6, 0.7], "beta": [0.4, 0.3]},
        )

        self.assertEqual(parameter_payload.y_axis.role, "parameter")
        self.assertEqual(phase_payload.y_axis.role, "phase_fraction")
        with self.assertRaisesRegex(ValueError, "series lengths"):
            parameter_evolution_payload([0.0, 1.0], {"scale": [1.0]})

    def test_matrix_payload_validates_square_labels_and_units(self) -> None:
        payload = MatrixPayload(
            "covariance",
            labels=("scale", "zero"),
            units=("dimensionless", "deg"),
            values=((1.0, 0.1), (0.1, 2.0)),
        )

        self.assertEqual(payload.kind, "covariance")
        with self.assertRaisesRegex(ValueError, "labels and units lengths"):
            MatrixPayload("correlation", labels=("scale",), units=("a", "b"), values=((1.0,),))

    def test_dependency_graph_payload_rejects_missing_node_references(self) -> None:
        graph = DependencyGraphPayload(
            nodes=(
                DependencyNode("scale", "Scale", "parameter"),
                DependencyNode("phase-a", "Phase A", "phase"),
            ),
            edges=(DependencyEdge("scale", "phase-a", "owned_by"),),
        )

        self.assertEqual(graph.edges[0].relationship, "owned_by")
        with self.assertRaisesRegex(ValueError, "existing node ids"):
            DependencyGraphPayload(
                nodes=(DependencyNode("scale", "Scale", "parameter"),),
                edges=(DependencyEdge("scale", "missing", "owned_by"),),
            )

    def test_reflection_browser_payload_preserves_rows_and_filters(self) -> None:
        payload = ReflectionBrowserPayload(
            rows=(
                ReflectionRow("phase-a", (1, 1, 0), 31.2, "deg", bank_id="bank-1", d_spacing=2.8),
            ),
            selected_phase_ids=("phase-a",),
        )

        self.assertEqual(payload.rows[0].position_units, "deg")
        with self.assertRaisesRegex(ValueError, "d_spacing"):
            ReflectionRow("phase-a", (1, 0, 0), 10.0, "deg", d_spacing=0.0)

    def test_mask_exclusion_editor_payload_validates_selection(self) -> None:
        payload = MaskExclusionEditorPayload(
            x_axis=PlotAxis("2theta", "deg", "x"),
            ranges=(ExclusionRange(10.0, 12.0, "beamstop"),),
            selected_range_index=0,
        )

        self.assertTrue(payload.editable)
        with self.assertRaisesRegex(ValueError, "out of range"):
            MaskExclusionEditorPayload(
                x_axis=PlotAxis("2theta", "deg", "x"),
                ranges=(),
                selected_range_index=0,
            )

    def test_publication_export_request_validates_format_and_dimensions(self) -> None:
        request = PublicationFigureExportRequest(
            "profile-main",
            "png",
            width=6.0,
            height=4.0,
            size_units="in",
            dpi=300,
            metadata={"creator": "unit-test"},
        )

        self.assertTrue(request.include_provenance)
        with self.assertRaisesRegex(ValueError, "positive"):
            PublicationFigureExportRequest("bad", "pdf", width=0.0, height=4.0, size_units="in")


if __name__ == "__main__":
    unittest.main()
