"""Magnetic neutron diffraction entities."""

from rietveld_next.neutron.magnetic.form_factors import (
    MagneticFormFactorCoefficients,
    available_magnetic_form_factor_ions,
    evaluate_magnetic_form_factor,
    lookup_magnetic_form_factor_coefficients,
    normalize_magnetic_ion_label,
)
from rietveld_next.neutron.magnetic.imports import (
    MagneticCifImportResult,
    RepresentationAnalysisImportPlaceholder,
    create_representation_analysis_placeholder,
    parse_magnetic_cif_skeleton,
)
from rietveld_next.neutron.magnetic.joint import (
    MagneticParameterGroupRecipe,
    MagneticReflectionFlag,
    MagneticTutorialDataset,
    NuclearMagneticPhaseCoupling,
    ReflectionCandidate,
    build_magnetic_parameter_group_recipes,
    create_magnetic_refinement_tutorial_dataset,
    flag_magnetic_reflections,
    generate_magnetic_report_section,
)
from rietveld_next.neutron.magnetic.moment import MagneticMoment
from rietveld_next.neutron.magnetic.propagation import PropagationVector
from rietveld_next.neutron.magnetic.symmetry import (
    MagneticSymmetryConstraint,
    create_collinear_moment_constraint,
    magnetic_moment_parameter_id,
    magnetic_moment_parameter_path,
)

__all__ = [
    "MagneticFormFactorCoefficients",
    "MagneticCifImportResult",
    "MagneticMoment",
    "MagneticParameterGroupRecipe",
    "MagneticReflectionFlag",
    "MagneticSymmetryConstraint",
    "MagneticTutorialDataset",
    "NuclearMagneticPhaseCoupling",
    "PropagationVector",
    "ReflectionCandidate",
    "RepresentationAnalysisImportPlaceholder",
    "available_magnetic_form_factor_ions",
    "build_magnetic_parameter_group_recipes",
    "create_collinear_moment_constraint",
    "create_magnetic_refinement_tutorial_dataset",
    "create_representation_analysis_placeholder",
    "evaluate_magnetic_form_factor",
    "flag_magnetic_reflections",
    "generate_magnetic_report_section",
    "lookup_magnetic_form_factor_coefficients",
    "magnetic_moment_parameter_id",
    "magnetic_moment_parameter_path",
    "normalize_magnetic_ion_label",
    "parse_magnetic_cif_skeleton",
]
