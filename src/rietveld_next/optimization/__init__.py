"""Optimization and residual numerical kernels."""

from rietveld_next.optimization.diagnostics import correlation_matrix_from_covariance, parameter_error_metrics
from rietveld_next.optimization.local import (
    ConvergenceReport,
    LocalOptimizerOptions,
    OptimizerSnapshot,
    coordinate_search_minimize,
)
from rietveld_next.optimization.objectives import (
    ObjectiveEvaluation,
    ObjectiveFunction,
    ObjectiveRegistry,
    invalid_model_evaluation,
    least_squares_evaluation,
    poisson_deviance_evaluation,
)
from rietveld_next.optimization.residuals import residual_vector
from rietveld_next.optimization.transforms import (
    BoundTransform,
    ParameterScale,
    scale_parameters,
    unscale_parameters,
)

__all__ = [
    "BoundTransform",
    "ConvergenceReport",
    "LocalOptimizerOptions",
    "ObjectiveEvaluation",
    "ObjectiveFunction",
    "ObjectiveRegistry",
    "OptimizerSnapshot",
    "ParameterScale",
    "coordinate_search_minimize",
    "correlation_matrix_from_covariance",
    "invalid_model_evaluation",
    "least_squares_evaluation",
    "parameter_error_metrics",
    "poisson_deviance_evaluation",
    "residual_vector",
    "scale_parameters",
    "unscale_parameters",
]
