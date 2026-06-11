"""Tests for project JSON Schema validation and serialization."""

from __future__ import annotations

import json
import unittest

from rietveld_next.core.model import (
    AxisType,
    Bounds,
    Constraint,
    ConstraintKind,
    CrystalStructure,
    Dataset,
    DetectorBank,
    Experiment,
    Histogram,
    Instrument,
    ModelValidationError,
    OptimizationMethod,
    OptimizationStrategy,
    ParameterPath,
    Phase,
    Project,
    Provenance,
    RadiationType,
    RefinementParameter,
    SequentialPoint,
    SequentialStudy,
    UnitMetadata,
)
from rietveld_next.core.schema import (
    SchemaValidationError,
    load_project_schema,
    project_from_json,
    project_to_json,
    validate_project_json,
    validate_project_mapping,
)


def build_realistic_project() -> Project:
    """Build a deterministic project that exercises schema-backed fields."""
    bank = DetectorBank(id="bank1", name="primary", axis=AxisType.TWO_THETA)
    instrument = Instrument(
        id="inst1",
        name="lab diffractometer",
        radiation=RadiationType.LAB_XRAY_CW,
        detector_banks=[bank],
        metadata={"wavelength_angstrom": 1.5406},
    )
    histogram = Histogram(
        id="hist1",
        dataset_id="dataset1",
        bank_id="bank1",
        x_uri="arrays/two_theta",
        y_uri="arrays/intensity",
        sigma_uri="arrays/sigma",
        phase_ids=["phase1"],
    )
    dataset = Dataset(
        id="dataset1",
        axis=AxisType.TWO_THETA,
        data_uri="arrays/profile",
        uncertainty_model="poisson",
        histograms=[histogram],
    )
    experiment = Experiment(
        id="exp1",
        radiation=RadiationType.LAB_XRAY_CW,
        instrument_id="inst1",
        datasets=[dataset],
        sample_environment={"temperature_K": 300.0},
    )
    phase = Phase(
        id="phase1",
        name="Silicon",
        crystal_structure=CrystalStructure(
            space_group="Fd-3m",
            cell={"a": 5.431, "alpha": 90.0, "beta": 90.0, "gamma": 90.0},
        ),
    )
    parameter = RefinementParameter(
        id="p_cell_a",
        path=ParameterPath("phase", "phase1", ("crystal_structure", "cell", "a")),
        value=5.431,
        refine=True,
        unit=UnitMetadata(symbol="angstrom", quantity="length", scale_to_si=1.0e-10),
        bounds=Bounds(lower=5.0, upper=6.0),
        owner_id="phase1",
    )
    return Project(
        id="project1",
        name="Schema serialization example",
        instruments=[instrument],
        experiments=[experiment],
        phases=[phase],
        parameters=[parameter],
        constraints=[
            Constraint(
                id="c_cell_a_positive",
                kind=ConstraintKind.INEQUALITY,
                expression="p_cell_a > 0",
                parameter_ids=["p_cell_a"],
            )
        ],
        strategies=[
            OptimizationStrategy(
                id="strategy1",
                method=OptimizationMethod.LEAST_SQUARES,
                parameter_ids=["p_cell_a"],
                diagnostics=["objective", "parameter_shift"],
            )
        ],
        studies=[
            SequentialStudy(
                id="study1",
                points=[SequentialPoint(id="point1", dataset_id="dataset1", variables={"temperature_K": 300.0})],
                shared_parameter_ids=["p_cell_a"],
            )
        ],
        provenance=Provenance(created_by="schema-test", created_at="2026-06-11T00:00:00Z"),
    )


class ProjectSchemaValidationTests(unittest.TestCase):
    """Schema-backed validation tests for project metadata."""

    def test_project_model_serializes_to_schema_valid_json(self) -> None:
        project = build_realistic_project()

        payload = project_to_json(project)
        loaded = project_from_json(payload)

        self.assertEqual(payload, project_to_json(loaded))
        self.assertEqual(loaded.schema_version, "1.0.0")
        self.assertEqual(loaded.instruments[0].detector_banks[0].id, "bank1")

    def test_project_mapping_validates_against_loaded_schema(self) -> None:
        schema = load_project_schema()
        data = build_realistic_project().to_schema_dict()

        validate_project_mapping(data, schema)

        self.assertIn("instruments", data)
        self.assertIn("strategies", data)
        self.assertIn("studies", data)

    def test_missing_required_field_reports_clear_schema_error(self) -> None:
        data = build_realistic_project().to_schema_dict()
        del data["schema_version"]

        with self.assertRaises(SchemaValidationError) as context:
            validate_project_mapping(data)

        self.assertEqual(context.exception.issues[0].path, "$")
        self.assertEqual(context.exception.issues[0].keyword, "required")
        self.assertIn("schema_version", context.exception.issues[0].message)

    def test_invalid_dataset_axis_reports_nested_path(self) -> None:
        data = build_realistic_project().to_schema_dict()
        data["experiments"][0]["datasets"][0]["axis"] = "invalid_axis"

        with self.assertRaises(SchemaValidationError) as context:
            validate_project_mapping(data)

        self.assertEqual(context.exception.issues[0].path, "$.experiments[0].datasets[0].axis")
        self.assertEqual(context.exception.issues[0].keyword, "enum")

    def test_invalid_schema_version_fails_pattern_validation(self) -> None:
        data = build_realistic_project().to_schema_dict()
        data["schema_version"] = "2.0.0"

        with self.assertRaises(SchemaValidationError) as context:
            validate_project_mapping(data)

        self.assertEqual(context.exception.issues[0].path, "$.schema_version")
        self.assertEqual(context.exception.issues[0].keyword, "pattern")

    def test_invalid_json_fails_before_model_deserialization(self) -> None:
        with self.assertRaises(SchemaValidationError) as context:
            validate_project_json("{not-json")

        self.assertEqual(context.exception.issues[0].path, "$")
        self.assertEqual(context.exception.issues[0].keyword, "json")

    def test_schema_validation_runs_before_reference_validation(self) -> None:
        payload = project_to_json(build_realistic_project())
        invalid_payload = validate_project_json(payload)
        invalid_payload["constraints"][0]["parameter_ids"] = ["missing"]
        invalid_json = json.dumps(invalid_payload, sort_keys=True, separators=(",", ":"))

        validate_project_mapping(invalid_payload)
        with self.assertRaises(ModelValidationError) as context:
            project_from_json(invalid_json)

        self.assertEqual(context.exception.code, "invalid_reference")


if __name__ == "__main__":
    unittest.main()
