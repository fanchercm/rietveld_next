# Numerical Engine Theory Guide

## Purpose

This guide records the current numerical-engine assumptions used by lightweight
foundation tests. It is a theory and auditability guide, not a complete
scientific validation claim.

## Scope

The current engine covers residual vectors, basic profile kernels, correction
helpers, sparse derivative utilities, covariance/correlation diagnostics, and
small deterministic optimizers.

## Non-Goals

The guide does not claim cross-software agreement. External validation is
tracked by [validation_baseline.md](validation_baseline.md) and future
reference datasets.

## Conventions

- Residuals use `observed - calculated`.
- Weighted residuals divide by positive standard uncertainties.
- Profile kernels document area and FWHM conventions in
  [numerical_kernels.md](numerical_kernels.md).
- Derivative checks compare analytic or structured derivatives against
  finite-difference fixtures using explicit tolerances.
- Diagnostics report singular or ill-conditioned cases instead of fabricating
  uncertainties.

## Example

For a synthetic residual smoke test, use a small array, record units, set a
fixed tolerance through `TolerancePolicy`, and include the fixture provenance in
the validation report.

## Related Files

- [numerical_kernels.md](numerical_kernels.md)
- [optimization.md](optimization.md)
- [validation_baseline.md](validation_baseline.md)
