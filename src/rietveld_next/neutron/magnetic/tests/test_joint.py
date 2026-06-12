"""Tests for joint nuclear-magnetic refinement helpers."""

from __future__ import annotations

import unittest

from rietveld_next.neutron.magnetic import (
    MagneticParameterGroupRecipe,
    NuclearMagneticPhaseCoupling,
    PropagationVector,
    ReflectionCandidate,
    build_magnetic_parameter_group_recipes,
    create_magnetic_refinement_tutorial_dataset,
    flag_magnetic_reflections,
    generate_magnetic_report_section,
)


class NuclearMagneticPhaseCouplingTests(unittest.TestCase):
    """Validate contribution toggles and intensity shape checks."""

    def test_coupling_combines_and_separates_contributions(self) -> None:
        coupling = NuclearMagneticPhaseCoupling(
            "phase1",
            nuclear_scale=2.0,
            magnetic_scale=0.5,
            magnetic_site_ids=("mn1",),
        )

        self.assertEqual(coupling.combine([10.0, 0.0], [2.0, 4.0]), (21.0, 2.0))
        self.assertEqual(
            coupling.separate_contributions([10.0], [2.0]),
            {"nuclear": (20.0,), "magnetic": (1.0,), "total": (21.0,)},
        )

    def test_coupling_toggle_removes_disabled_contribution(self) -> None:
        coupling = NuclearMagneticPhaseCoupling(
            "phase1",
            nuclear_enabled=False,
            magnetic_site_ids=("mn1",),
        )

        self.assertEqual(coupling.combine([10.0], [2.0]), (2.0,))

    def test_coupling_rejects_negative_or_mismatched_intensity(self) -> None:
        coupling = NuclearMagneticPhaseCoupling("phase1")

        with self.assertRaisesRegex(ValueError, "same length"):
            coupling.combine([1.0], [1.0, 2.0])
        with self.assertRaisesRegex(ValueError, "non-negative"):
            coupling.combine([1.0], [-1.0])


class MagneticReflectionFlaggingTests(unittest.TestCase):
    """Validate deterministic magnetic reflection classification."""

    def test_reflection_flagging_identifies_nuclear_and_satellite_peaks(self) -> None:
        vector = PropagationVector("k1", (0.5, 0.0, 0.0))
        flags = flag_magnetic_reflections(
            (
                ReflectionCandidate((1.0, 0.0, 0.0), label="100"),
                ReflectionCandidate((0.5, 0.0, 0.0), label="000+k"),
                ReflectionCandidate((1.5, 0.0, 0.0), label="200-k"),
                ReflectionCandidate((0.25, 0.0, 0.0), label="unindexed"),
            ),
            (vector,),
        )

        self.assertEqual([flag.kind for flag in flags], [
            "nuclear",
            "magnetic_satellite",
            "magnetic_satellite",
            "unindexed",
        ])
        self.assertEqual(flags[1].propagation_vector_id, "k1")
        self.assertEqual(flags[1].satellite_sign, 1)
        self.assertEqual(flags[2].satellite_sign, -1)

    def test_zero_propagation_vector_marks_mixed_reflection(self) -> None:
        flags = flag_magnetic_reflections(
            ((1.0, 0.0, 0.0),),
            (PropagationVector("k0", (0.0, 0.0, 0.0)),),
        )

        self.assertEqual(flags[0].kind, "mixed_nuclear_magnetic")

    def test_reflection_flagging_rejects_invalid_tolerance(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            flag_magnetic_reflections(((1.0, 0.0, 0.0),), (), tolerance_rlu=0.0)


class MagneticTutorialAndReportTests(unittest.TestCase):
    """Validate deterministic tutorial fixture and report section generation."""

    def test_tutorial_dataset_contains_separate_contributions(self) -> None:
        dataset = create_magnetic_refinement_tutorial_dataset()

        self.assertEqual(dataset.dataset_id, "m25_synthetic_mno_collinear")
        self.assertEqual(dataset.calculated_intensity, (100.0, 12.0, 9.0, 36.0))
        self.assertEqual(
            [flag.kind for flag in dataset.reflection_flags],
            ["nuclear", "magnetic_satellite", "magnetic_satellite", "nuclear"],
        )
        self.assertEqual(dataset.to_dict()["notes"][1], "Not cross-software validation of magnetic structure factors.")

    def test_report_section_is_deterministic_and_separates_intensity(self) -> None:
        dataset = create_magnetic_refinement_tutorial_dataset()

        report = generate_magnetic_report_section(dataset)

        self.assertIn("## Magnetic refinement", report)
        self.assertIn("- Nuclear relative intensity sum: `136`", report)
        self.assertIn("- Magnetic relative intensity sum: `21`", report)
        self.assertIn("- magnetic_satellite: `2`", report)
        self.assertIn("Stage 1: `phase_mno:magnetic_scale`", report)

    def test_report_rejects_non_dataset(self) -> None:
        with self.assertRaisesRegex(ValueError, "MagneticTutorialDataset"):
            generate_magnetic_report_section("not a dataset")  # type: ignore[arg-type]


class MagneticParameterGroupRecipeTests(unittest.TestCase):
    """Validate staged magnetic parameter recipe construction."""

    def test_recipes_are_staged_and_bound_moment_components(self) -> None:
        recipes = build_magnetic_parameter_group_recipes("phase1", ("mn1", "mn2"))

        self.assertEqual([recipe.stage for recipe in recipes], [1, 2, 3])
        self.assertEqual(recipes[0].parameter_ids, ("p_phase_phase1_magnetic_scale",))
        self.assertEqual(
            recipes[1].parameter_ids,
            (
                "p_phase_phase1_magnetic_structure_sites_mn1_moment_mz",
                "p_phase_phase1_magnetic_structure_sites_mn2_moment_mz",
            ),
        )
        self.assertEqual(
            recipes[2].bounds[
                "p_phase_phase1_magnetic_structure_sites_mn1_moment_mx"
            ],
            (-10.0, 10.0),
        )

    def test_recipe_rejects_bounds_for_unknown_parameter(self) -> None:
        with self.assertRaisesRegex(ValueError, "not in parameter_ids"):
            MagneticParameterGroupRecipe(
                recipe_id="bad",
                stage=1,
                label="Bad",
                parameter_ids=("p_a",),
                default_action="refine",
                rationale="test",
                bounds={"p_b": (0.0, 1.0)},
            )

    def test_recipe_builder_rejects_empty_sites(self) -> None:
        with self.assertRaisesRegex(ValueError, "site_ids"):
            build_magnetic_parameter_group_recipes("phase1", ())


if __name__ == "__main__":
    unittest.main()
