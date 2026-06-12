"""Tests for magnetic symmetry parameter-graph helpers."""

from __future__ import annotations

import unittest

from rietveld_next.core.model import ConstraintKind
from rietveld_next.neutron.magnetic import (
    MagneticSymmetryConstraint,
    create_collinear_moment_constraint,
    magnetic_moment_parameter_id,
    magnetic_moment_parameter_path,
)


class MagneticSymmetryTests(unittest.TestCase):
    """Validate magnetic moment parameter paths and symbolic constraints."""

    def test_magnetic_moment_parameter_path_is_canonical(self) -> None:
        path = magnetic_moment_parameter_path("phase1", "mn1", "Mz")

        self.assertEqual(str(path), "phase/phase1/magnetic_structure/sites/mn1/moment/mz")
        self.assertEqual(
            magnetic_moment_parameter_id("phase1", "mn1", "mz"),
            "p_phase_phase1_magnetic_structure_sites_mn1_moment_mz",
        )

    def test_collinear_constraint_converts_to_core_constraint(self) -> None:
        constraint = create_collinear_moment_constraint(
            constraint_id="c_mn_flip",
            phase_id="phase1",
            reference_site_id="mn1",
            constrained_site_id="mn2",
            component="mx",
            multiplier=-1.0,
            operation_label="time-reversal mate",
        )

        self.assertEqual(
            constraint.parameter_ids,
            (
                "p_phase_phase1_magnetic_structure_sites_mn2_moment_mx",
                "p_phase_phase1_magnetic_structure_sites_mn1_moment_mx",
            ),
        )
        self.assertEqual(
            constraint.expression,
            "p_phase_phase1_magnetic_structure_sites_mn2_moment_mx = -1 * "
            "p_phase_phase1_magnetic_structure_sites_mn1_moment_mx",
        )
        core_constraint = constraint.to_core_constraint()
        self.assertEqual(core_constraint.kind, ConstraintKind.SYMBOLIC)
        self.assertEqual(core_constraint.id, "c_mn_flip")
        self.assertEqual(core_constraint.parameter_ids, list(constraint.parameter_ids))

    def test_symmetry_constraint_serialization_is_deterministic(self) -> None:
        constraint = MagneticSymmetryConstraint(
            constraint_id="c_link",
            parameter_ids=("p_b", "p_a"),
            expression="p_b = p_a",
            operation_label="identity",
            metadata={"site": "mn1", "component": "mz"},
        )

        self.assertEqual(
            constraint.to_dict(),
            {
                "constraint_id": "c_link",
                "kind": "magnetic_symmetry",
                "parameter_ids": ["p_b", "p_a"],
                "expression": "p_b = p_a",
                "operation_label": "identity",
                "units": "bohr_magneton",
                "metadata": {"component": "mz", "site": "mn1"},
            },
        )

    def test_symmetry_helpers_reject_invalid_inputs(self) -> None:
        with self.assertRaisesRegex(ValueError, "component"):
            magnetic_moment_parameter_path("phase1", "mn1", "ma")
        with self.assertRaisesRegex(ValueError, "finite"):
            create_collinear_moment_constraint(
                constraint_id="c_bad",
                phase_id="phase1",
                reference_site_id="mn1",
                constrained_site_id="mn2",
                component="mz",
                multiplier=float("inf"),
                operation_label="bad",
            )
        with self.assertRaisesRegex(ValueError, "parameter_ids"):
            MagneticSymmetryConstraint("c_empty", (), "p = 0", "identity")


if __name__ == "__main__":
    unittest.main()
