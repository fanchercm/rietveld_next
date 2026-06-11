"""Tests for typed core model entities."""

from __future__ import annotations

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


def build_project() -> Project:
    """Build a small deterministic project graph for tests."""
    bank = DetectorBank(id="bank1", axis=AxisType.TWO_THETA)
    instrument = Instrument(id="inst1", radiation=RadiationType.LAB_XRAY_CW, detector_banks=[bank])
    histogram = Histogram(
        id="hist1",
        dataset_id="dataset1",
        bank_id="bank1",
        x_uri="arrays/x",
        y_uri="arrays/y",
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
    )
    constraint = Constraint(
        id="c_cell_a_positive",
        kind=ConstraintKind.INEQUALITY,
        expression="p_cell_a > 0",
        parameter_ids=["p_cell_a"],
    )
    strategy = OptimizationStrategy(
        id="strategy1",
        method=OptimizationMethod.LEAST_SQUARES,
        parameter_ids=["p_cell_a"],
    )
    study = SequentialStudy(
        id="study1",
        points=[SequentialPoint(id="point1", dataset_id="dataset1", variables={"temperature_K": 300.0})],
        shared_parameter_ids=["p_cell_a"],
    )
    return Project(
        id="project1",
        name="Core model smoke project",
        experiments=[experiment],
        phases=[phase],
        parameters=[parameter],
        instruments=[instrument],
        constraints=[constraint],
        strategies=[strategy],
        studies=[study],
        provenance=Provenance(created_by="unit-test"),
    )


class CoreModelEntityTests(unittest.TestCase):
    """Validation and round-trip tests for the core model graph."""

    def test_project_round_trip_json_is_stable(self) -> None:
        project = build_project()

        payload = project.to_json()
        loaded = Project.from_json(payload)

        self.assertEqual(payload, loaded.to_json())
        self.assertEqual(loaded.parameter_map()["p_cell_a"].value, 5.431)

    def test_schema_compatibility_required_fields_are_emitted(self) -> None:
        payload = build_project().to_schema_dict()

        self.assertEqual(payload["schema_version"], "1.0.0")
        self.assertIn("id", payload)
        self.assertIsInstance(payload["experiments"], list)
        self.assertIsInstance(payload["phases"], list)
        self.assertIsInstance(payload["parameters"], list)
        self.assertEqual(payload["parameters"][0]["units"], "angstrom")
        self.assertEqual(payload["parameters"][0]["bounds"], [5.0, 6.0])

    def test_missing_required_field_reports_structured_error(self) -> None:
        with self.assertRaises(ModelValidationError) as context:
            Project.from_dict({"id": "project1", "experiments": [], "phases": [], "parameters": []})

        self.assertEqual(context.exception.code, "missing_required_field")
        self.assertIn("schema_version", context.exception.details["missing"])

    def test_invalid_entity_id_is_rejected(self) -> None:
        with self.assertRaises(ModelValidationError) as context:
            Phase(id="1bad", name="Invalid", crystal_structure=CrystalStructure())

        self.assertEqual(context.exception.code, "invalid_id")

    def test_invalid_bounds_are_rejected(self) -> None:
        with self.assertRaises(ModelValidationError) as context:
            RefinementParameter(
                id="p_bad",
                path=ParameterPath("phase", "phase1", ("crystal_structure", "cell", "a")),
                value=7.0,
                refine=True,
                bounds=Bounds(lower=5.0, upper=6.0),
            )

        self.assertEqual(context.exception.code, "value_out_of_bounds")

    def test_constraint_references_must_target_existing_parameters(self) -> None:
        project = build_project()
        bad_constraint = Constraint(
            id="c_bad",
            kind=ConstraintKind.EQUALITY,
            expression="missing == 0",
            parameter_ids=["missing"],
        )

        with self.assertRaises(ModelValidationError) as context:
            Project(
                id=project.id,
                experiments=project.experiments,
                phases=project.phases,
                parameters=project.parameters,
                instruments=project.instruments,
                constraints=[bad_constraint],
            )

        self.assertEqual(context.exception.code, "invalid_reference")
        self.assertEqual(context.exception.details["parameter_ids"], ["missing"])

    def test_parameter_path_canonical_string_is_stable(self) -> None:
        path = ParameterPath.parse("phase/phase1/crystal_structure/cell/a")

        self.assertEqual(str(path), "phase/phase1/crystal_structure/cell/a")
        self.assertEqual(path.owner_type, "phase")
        self.assertEqual(path.owner_id, "phase1")
        self.assertEqual(path.segments, ("crystal_structure", "cell", "a"))

    def test_project_diff_reports_changed_entity_ids(self) -> None:
        original = build_project()
        changed_parameter = RefinementParameter(
            id="p_cell_a",
            path=ParameterPath("phase", "phase1", ("crystal_structure", "cell", "a")),
            value=5.432,
            refine=True,
            unit=UnitMetadata(symbol="angstrom", quantity="length", scale_to_si=1.0e-10),
            bounds=Bounds(lower=5.0, upper=6.0),
        )
        changed = Project(
            id=original.id,
            experiments=original.experiments,
            phases=original.phases,
            parameters=[changed_parameter],
            instruments=original.instruments,
            constraints=original.constraints,
            strategies=original.strategies,
            studies=original.studies,
        )

        self.assertEqual(original.diff(changed), {"parameters": ["p_cell_a"]})


if __name__ == "__main__":
    unittest.main()
