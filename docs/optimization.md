# Optimization Foundation

This document covers the first Batch C optimization infrastructure. The
implementation is dependency-free and generic; it is not coupled to diffraction
models, UI, AI, SciPy, or Rust backends.

## Objective Evaluations

Location: `src/rietveld_next/optimization/objectives.py`

Public API:

```python
ObjectiveEvaluation(parameters, objective_value, residuals=(), status="ok")
ObjectiveRegistry()
least_squares_evaluation(parameters, residuals, loss="linear", loss_scale=1.0)
poisson_deviance_evaluation(parameters, observed, expected)
invalid_model_evaluation(parameters, message, **diagnostics)
```

Behavior:

- Objective evaluations are structured and JSON-compatible.
- Valid objective values are finite and non-negative.
- Invalid model states use `status="invalid"` with a large finite penalty and
  diagnostic metadata.
- Least-squares residual convention follows `residual_vector`: observed minus
  calculated, or caller-supplied residuals in deterministic order.
- Robust losses currently include `linear`, `huber`, and `soft_l1`.

Poisson deviance:

```text
D = 2 * sum(expected_i - observed_i + observed_i * log(observed_i / expected_i))
```

For zero observed counts, the contribution is `2 * expected_i`.

## Scaling And Bounds

Location: `src/rietveld_next/optimization/transforms.py`

Public API:

```python
ParameterScale(offset=0.0, scale=1.0)
BoundTransform(lower=None, upper=None)
scale_parameters(values, scales)
unscale_parameters(values, scales)
```

Bounds:

- No bounds: identity transform.
- Lower-only: `x = lower + exp(u)`.
- Upper-only: `x = upper - exp(u)`.
- Finite lower/upper: logistic transform.

Inverse transforms require values strictly inside active bounds, including
one-sided bounds. Inclusive endpoint validation remains available through
`validate_value`.

## Local Optimizer

Location: `src/rietveld_next/optimization/local.py`

Public API:

```python
LocalOptimizerOptions(max_iterations=100, initial_step=1.0, tolerance=1e-6)
coordinate_search_minimize(objective, initial_parameters, bounds=None, options=None)
ConvergenceReport
OptimizerSnapshot
```

The local optimizer is deterministic coordinate search in physical parameter
units. It is intended for small synthetic tests, smoke benchmarks, and adapter
contract validation. It should not be used as the production Rietveld
least-squares engine.

Returned convergence reports include:

- status and message
- convergence boolean
- iterations and objective evaluations
- final objective value
- final parameter vector
- rollback snapshots
- diagnostic metadata

Failure modes are structured. Invalid initial objective evaluations return
`status="invalid_initial_model"`. Exhausted iterations return
`status="max_iterations"`.

## Diagnostics

Location: `src/rietveld_next/optimization/diagnostics.py`

Public API:

```python
LabeledMatrix
parameter_error_metrics(parameters, reference)
covariance_from_jacobian(
    jacobian,
    residual_variance,
    parameter_labels,
    parameter_units=None,
)
correlation_matrix_from_covariance(covariance)
labeled_correlation_matrix_from_covariance(
    covariance,
    parameter_labels,
    parameter_units=None,
)
```

Diagnostics validate finite inputs and report clear errors for length mismatch,
non-square covariance matrices, and non-positive variances. The labeled
covariance and correlation helpers preserve parameter labels and units in their
result records. Singular or underdetermined covariance estimates return
`status="singular"` with warnings instead of reporting misleading
uncertainties.

Covariance estimation:

```text
C = residual_variance * inv(J^T J)
```

This dense normal-equation helper is intended only for small synthetic
diagnostics and validation fixtures. It is not a production sparse
least-squares covariance engine.

## Sparse Jacobians And Derivative Checks

Location: `src/rietveld_next/optimization/jacobian.py`

Public API:

```python
SparseJacobian(row_count, column_count, entries=...)
SparseJacobianEntry(row, column, value)
finite_difference_jacobian(residual_function, parameters, ...)
scale_residual_derivative(unscaled_calculated, sigma=None)
polynomial_background_residual_jacobian(x_values, degree, ...)
gradient_check(residual_function, parameters, analytic_jacobian, ...)
```

Conventions:

- Rows are residuals and columns are parameters.
- Derivatives use residual units divided by parameter units.
- The residual convention remains `observed - calculated`.
- Sparse storage is deterministic coordinate-list form sorted by `(row, column)`.

The finite-difference fallback is for small synthetic checks and gradient-test
utilities. It is not a large sparse production differentiator.

## Uncertainty Diagnostics

Location: `src/rietveld_next/optimization/uncertainty.py`

Public API:

```python
covariance_from_jacobian(jacobian, ...)
covariance_from_normal_matrix(normal_matrix, ...)
correlation_from_covariance(covariance, ...)
```

These helpers return structured covariance/correlation diagnostics. Singular
and ill-conditioned systems return statuses and warnings without reporting
misleading uncertainty matrices. Parameter labels and units are carried through
the result objects for auditability.

## Global Search And Placeholders

Location: `src/rietveld_next/optimization/global_search.py`

Public API:

```python
differential_evolution_minimize(objective, bounds, ...)
simulated_annealing_minimize(objective, initial_parameters, ...)
multi_start_minimize(objective, bounds, ...)
bayesian_optimization_placeholder(objective, bounds, ...)
mcmc_uncertainty_placeholder(log_posterior, initial_parameters, ...)
```

Global-search adapters use explicit pseudo-random seeds and tiny deterministic
defaults. Bayesian optimization and MCMC are intentionally placeholder APIs:
they return structured `not_implemented` records and do not call user
objectives or fabricate samples.

## Validation Limits

Tests use analytic and synthetic functions only. No cross-software refinement
validation is claimed. SciPy trust-region, Levenberg-Marquardt, Rust optimizer
traits, JAX automatic differentiation, and production covariance estimation
remain follow-up work.
