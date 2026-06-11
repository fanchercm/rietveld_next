# Numerical Kernels

This document covers the first dependency-free numerical reference kernels for
Rietveld Next. These functions live under `src/rietveld_next/` and are intended
to be small, deterministic, and benchmarkable. They are not optimized backends.

## Gaussian Profile

Location: `src/rietveld_next/diffraction/profiles.py`

Function:

```python
gaussian_profile(x, *, center, fwhm, area=1.0)
```

The function evaluates an area-scaled Gaussian peak profile:

```text
G(x) = area * sqrt(4 ln(2) / pi) / fwhm
       * exp(-4 ln(2) * ((x - center) / fwhm)^2)
```

Assumptions:

- `x`, `center`, and `fwhm` use the same axis units.
- Supported axis units include degrees two-theta, TOF microseconds,
  d-spacing angstroms, or energy keV.
- `fwhm` must be positive.
- `area` is the integrated peak area. Negative area is permitted only for
  callers intentionally modeling signed residual components.
- The returned values are intensity per axis unit.

Validation:

- All scalar inputs must be finite real numbers.
- Axis values must be a sequence of finite real numbers.
- Empty axes return an empty list.

## Lorentzian Profile

Location: `src/rietveld_next/diffraction/profiles.py`

Function:

```python
lorentzian_profile(x, *, center, fwhm, area=1.0)
```

The function evaluates an area-scaled Lorentzian/Cauchy peak profile:

```text
L(x) = area * (0.5 * fwhm / pi)
       / ((x - center)^2 + (0.5 * fwhm)^2)
```

Assumptions:

- `x`, `center`, and `fwhm` use the same axis units.
- `fwhm` must be positive.
- The returned values are intensity per axis unit and integrate to `area`
  over an infinite domain.

## Pseudo-Voigt Profile

Location: `src/rietveld_next/diffraction/profiles.py`

Functions:

```python
pseudo_voigt_profile(x, *, center, fwhm, eta, area=1.0)
thompson_cox_hastings_profile(
    x,
    *,
    center,
    gaussian_fwhm,
    lorentzian_fwhm,
    area=1.0,
)
```

The pseudo-Voigt profile is a linear combination of area-scaled Lorentzian
and Gaussian profiles:

```text
pV(x) = eta * L(x, fwhm) + (1 - eta) * G(x, fwhm)
```

`eta` is the Lorentzian mixing fraction and must be in `[0, 1]`.

The Thompson-Cox-Hastings helper uses the standard pseudo-Voigt approximation:

```text
H = (H_G^5 + 2.69269 H_G^4 H_L + 2.42843 H_G^3 H_L^2
     + 4.47163 H_G^2 H_L^3 + 0.07842 H_G H_L^4 + H_L^5)^(1/5)
eta = 1.36603 r - 0.47719 r^2 + 0.11116 r^3, r = H_L / H
```

Assumptions and limits:

- Component FWHM values use the same axis units as `x`.
- Thompson-Cox-Hastings component widths must be non-negative, and at least
  one component width must be positive.
- Tests cover synthetic limiting cases only. Cross-software validation is not
  claimed yet.

## Peak Windowing And Reflection Batching

Location: `src/rietveld_next/diffraction/profiles.py`

Functions and data records:

```python
peak_window_indices(x, *, center, fwhm, width_factor=8.0)
Reflection(id, center, fwhm, area=1.0)
plan_reflection_batches(reflections, *, max_batch_size)
```

`peak_window_indices` returns a Python slice boundary pair selecting values
within `center +/- width_factor * fwhm`. The input axis must be sorted in
non-decreasing order.

`plan_reflection_batches` sorts reflections by `(center, id)` before grouping
them into fixed-size batches. This makes execution plans reproducible even when
callers supply reflections in different input orders.

## Residual Vector

Location: `src/rietveld_next/optimization/residuals.py`

Function:

```python
residual_vector(observed, calculated, sigma=None)
```

The unweighted residual convention is:

```text
r_i = observed_i - calculated_i
```

When standard uncertainties are supplied:

```text
r_i = (observed_i - calculated_i) / sigma_i
```

Assumptions:

- Observed, calculated, and `sigma` values are in compatible intensity units.
- `sigma` represents one-standard-deviation uncertainty and must be positive.
- Residuals preserve the deterministic input order.

Validation:

- All values must be finite real numbers.
- Input lengths must match.
- Empty observed/calculated sequences return an empty list.
- Non-positive uncertainty values raise `ValueError`.

## Precision And Validation Limits

These kernels use Python `float` arithmetic. Tests cover known analytic
relationships and small synthetic data. They do not claim cross-software
validation against GSAS-II, FullProf, TOPAS, or facility datasets.

## Validation Command

```bash
PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next
```
