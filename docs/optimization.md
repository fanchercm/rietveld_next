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
parameter_error_metrics(parameters, reference)
correlation_matrix_from_covariance(covariance)
```

Diagnostics validate finite inputs and report clear errors for length mismatch,
non-square covariance matrices, and non-positive variances.

## Validation Limits

Tests use analytic and synthetic functions only. No cross-software refinement
validation is claimed. SciPy trust-region, Levenberg-Marquardt, Rust optimizer
traits, sparse Jacobians, and production covariance estimation remain follow-up
work.
