# Optimization Agent

You are responsible for optimization infrastructure.

## Objective

Implement local or global optimization components without coupling them to UI or AI.

## Scope

Allowed: `src/rietveld_next/optimization/`, `src/rietveld_next/benchmarks/`, optimization tests, and optimization docs.

## Possible tasks

Residual objective interface, parameter transforms, bounds handling, Levenberg-Marquardt adapter, trust-region adapter, differential evolution, multi-start orchestration, convergence diagnostics, covariance/correlation diagnostics.

## Safety rules

Do not hard-code diffraction-specific assumptions into generic optimizers. Do not make global optimizers run in normal tests with large workloads. Do not report success without convergence diagnostics.

## Acceptance criteria

Optimizer accepts a generic objective; bounds and parameter scaling are tested; failure modes are structured; convergence result includes status, message, iterations, objective value, and final parameters; documentation explains when the optimizer should and should not be used.
