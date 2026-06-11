"""Peak profile kernels and planning helpers for diffraction calculations.

The kernels in this module are deliberately small and dependency-free so they
can serve as reference implementations for tests and later optimized backends.
"""

from __future__ import annotations

from dataclasses import dataclass
import bisect
import math
from collections.abc import Sequence


_GAUSSIAN_LOG2_FACTOR = 4.0 * math.log(2.0)
_GAUSSIAN_NORMALIZATION = math.sqrt(_GAUSSIAN_LOG2_FACTOR / math.pi)


def gaussian_profile(
    x: Sequence[float],
    *,
    center: float,
    fwhm: float,
    area: float = 1.0,
) -> list[float]:
    """Evaluate an area-scaled Gaussian peak profile.

    The independent axis values in ``x`` and the ``center`` and ``fwhm``
    arguments must use the same axis units, such as degrees two-theta, TOF
    microseconds, d-spacing angstroms, or energy keV. The returned profile has
    intensity per axis unit, so its numerical integral is approximately
    ``area`` when sampled densely enough.

    Mathematical expression:

    ```text
    G(x) = area * sqrt(4 ln(2) / pi) / fwhm
           * exp(-4 ln(2) * ((x - center) / fwhm)^2)
    ```

    Args:
        x: Axis positions where the profile is evaluated.
        center: Peak center in the same units as ``x``.
        fwhm: Full width at half maximum. Must be positive.
        area: Integrated peak area. May be negative only when callers are
            intentionally modeling signed residual components.

    Returns:
        Profile values at each point in ``x``.

    Raises:
        ValueError: If any input is non-finite, ``fwhm`` is not positive, or
            ``x`` is not a sequence of finite numeric values.

    Example:
        >>> gaussian_profile([0.0], center=0.0, fwhm=2.0)
        [0.46971863934982566]
    """
    axis = _finite_sequence(x, "x")
    center_value = _finite_float(center, "center")
    fwhm_value = _finite_float(fwhm, "fwhm")
    area_value = _finite_float(area, "area")
    if fwhm_value <= 0.0:
        raise ValueError(f"fwhm must be positive, got {fwhm_value!r}.")

    scale = area_value * _GAUSSIAN_NORMALIZATION / fwhm_value
    return [
        scale * math.exp(-_GAUSSIAN_LOG2_FACTOR * ((axis_value - center_value) / fwhm_value) ** 2)
        for axis_value in axis
    ]


def lorentzian_profile(
    x: Sequence[float],
    *,
    center: float,
    fwhm: float,
    area: float = 1.0,
) -> list[float]:
    """Evaluate an area-scaled Lorentzian/Cauchy peak profile.

    The independent axis values in ``x`` and the ``center`` and ``fwhm``
    arguments must use the same axis units. The returned profile has intensity
    per axis unit and integrates to ``area`` over an infinite domain.

    Mathematical expression:

    ```text
    L(x) = area * (0.5 * fwhm / pi)
           / ((x - center)^2 + (0.5 * fwhm)^2)
    ```

    Args:
        x: Axis positions where the profile is evaluated.
        center: Peak center in the same units as ``x``.
        fwhm: Full width at half maximum. Must be positive.
        area: Integrated peak area.

    Returns:
        Profile values at each point in ``x``.

    Raises:
        ValueError: If any input is non-finite, ``fwhm`` is not positive, or
            ``x`` is not a sequence of finite numeric values.

    Example:
        >>> lorentzian_profile([0.0], center=0.0, fwhm=2.0)
        [0.3183098861837907]
    """
    axis = _finite_sequence(x, "x")
    center_value = _finite_float(center, "center")
    fwhm_value = _finite_float(fwhm, "fwhm")
    area_value = _finite_float(area, "area")
    if fwhm_value <= 0.0:
        raise ValueError(f"fwhm must be positive, got {fwhm_value!r}.")

    half_width = 0.5 * fwhm_value
    scale = area_value * half_width / math.pi
    return [scale / ((axis_value - center_value) ** 2 + half_width**2) for axis_value in axis]


def pseudo_voigt_profile(
    x: Sequence[float],
    *,
    center: float,
    fwhm: float,
    eta: float,
    area: float = 1.0,
) -> list[float]:
    """Evaluate an area-scaled pseudo-Voigt profile.

    This reference kernel uses a linear combination of area-normalized
    Lorentzian and Gaussian terms with a shared full width at half maximum:

    ```text
    pV(x) = eta * L(x, fwhm) + (1 - eta) * G(x, fwhm)
    ```

    Args:
        x: Axis positions where the profile is evaluated.
        center: Peak center in the same units as ``x``.
        fwhm: Shared full width at half maximum. Must be positive.
        eta: Lorentzian mixing fraction on ``[0, 1]``.
        area: Integrated peak area.

    Returns:
        Profile values at each point in ``x``.

    Raises:
        ValueError: If inputs are non-finite, ``fwhm`` is not positive, or
            ``eta`` is outside ``[0, 1]``.

    Example:
        >>> pseudo_voigt_profile([0.0], center=0.0, fwhm=2.0, eta=1.0)
        [0.3183098861837907]
    """
    eta_value = _mixing_fraction(eta, "eta")
    gaussian = gaussian_profile(x, center=center, fwhm=fwhm, area=area)
    lorentzian = lorentzian_profile(x, center=center, fwhm=fwhm, area=area)
    return [
        eta_value * lorentzian_value + (1.0 - eta_value) * gaussian_value
        for gaussian_value, lorentzian_value in zip(gaussian, lorentzian, strict=True)
    ]


def thompson_cox_hastings_profile(
    x: Sequence[float],
    *,
    center: float,
    gaussian_fwhm: float,
    lorentzian_fwhm: float,
    area: float = 1.0,
) -> list[float]:
    """Evaluate the Thompson-Cox-Hastings pseudo-Voigt approximation.

    The Gaussian and Lorentzian component widths must use the same axis units
    as ``x`` and ``center``. This approximation first computes an effective
    pseudo-Voigt FWHM and Lorentzian mixing fraction, then delegates to
    :func:`pseudo_voigt_profile`.

    Approximation:

    ```text
    H = (H_G^5 + 2.69269 H_G^4 H_L + 2.42843 H_G^3 H_L^2
         + 4.47163 H_G^2 H_L^3 + 0.07842 H_G H_L^4 + H_L^5)^(1/5)
    eta = 1.36603 r - 0.47719 r^2 + 0.11116 r^3, r = H_L / H
    ```

    Args:
        x: Axis positions where the profile is evaluated.
        center: Peak center in the same units as ``x``.
        gaussian_fwhm: Gaussian contribution to FWHM. Must be non-negative.
        lorentzian_fwhm: Lorentzian contribution to FWHM. Must be non-negative.
        area: Integrated peak area.

    Returns:
        Profile values at each point in ``x``.

    Raises:
        ValueError: If inputs are non-finite, either component width is
            negative, or both component widths are zero.

    Example:
        >>> thompson_cox_hastings_profile([0.0], center=0.0, gaussian_fwhm=2.0, lorentzian_fwhm=0.0)
        [0.46971863934982566]
    """
    gaussian_width = _finite_float(gaussian_fwhm, "gaussian_fwhm")
    lorentzian_width = _finite_float(lorentzian_fwhm, "lorentzian_fwhm")
    if gaussian_width < 0.0:
        raise ValueError(f"gaussian_fwhm must be non-negative, got {gaussian_width!r}.")
    if lorentzian_width < 0.0:
        raise ValueError(f"lorentzian_fwhm must be non-negative, got {lorentzian_width!r}.")
    if gaussian_width == 0.0 and lorentzian_width == 0.0:
        raise ValueError("At least one of gaussian_fwhm or lorentzian_fwhm must be positive.")

    effective_fwhm = (
        gaussian_width**5
        + 2.69269 * gaussian_width**4 * lorentzian_width
        + 2.42843 * gaussian_width**3 * lorentzian_width**2
        + 4.47163 * gaussian_width**2 * lorentzian_width**3
        + 0.07842 * gaussian_width * lorentzian_width**4
        + lorentzian_width**5
    ) ** 0.2
    ratio = lorentzian_width / effective_fwhm
    eta = _clamp_unit_interval(1.36603 * ratio - 0.47719 * ratio**2 + 0.11116 * ratio**3)
    return pseudo_voigt_profile(x, center=center, fwhm=effective_fwhm, eta=eta, area=area)


def peak_window_indices(
    x: Sequence[float],
    *,
    center: float,
    fwhm: float,
    width_factor: float = 8.0,
) -> tuple[int, int]:
    """Return an inclusive-exclusive slice covering a finite peak window.

    The axis must be sorted in non-decreasing order and use the same units as
    ``center`` and ``fwhm``. The selected window covers:

    ```text
    center - width_factor * fwhm <= x <= center + width_factor * fwhm
    ```

    Args:
        x: Sorted axis positions.
        center: Peak center in the same units as ``x``.
        fwhm: Full width at half maximum. Must be positive.
        width_factor: Positive multiplier controlling the window half width.

    Returns:
        ``(start, stop)`` indices suitable for slicing ``x[start:stop]``.

    Raises:
        ValueError: If inputs are non-finite, ``fwhm`` or ``width_factor`` is
            not positive, or ``x`` is not sorted.

    Example:
        >>> peak_window_indices([-2.0, -1.0, 0.0, 1.0, 2.0], center=0.0, fwhm=0.5, width_factor=2.0)
        (1, 4)
    """
    axis = _finite_sequence(x, "x")
    center_value = _finite_float(center, "center")
    fwhm_value = _finite_float(fwhm, "fwhm")
    width_factor_value = _finite_float(width_factor, "width_factor")
    if fwhm_value <= 0.0:
        raise ValueError(f"fwhm must be positive, got {fwhm_value!r}.")
    if width_factor_value <= 0.0:
        raise ValueError(f"width_factor must be positive, got {width_factor_value!r}.")
    _require_sorted(axis, "x")

    half_window = width_factor_value * fwhm_value
    start = bisect.bisect_left(axis, center_value - half_window)
    stop = bisect.bisect_right(axis, center_value + half_window)
    return start, stop


@dataclass(frozen=True)
class Reflection:
    """Minimal reflection metadata needed for deterministic profile batching.

    Args:
        id: Stable reflection identifier.
        center: Reflection center in the target axis units.
        fwhm: Full width at half maximum in the target axis units.
        area: Integrated intensity or scale proxy.

    Raises:
        ValueError: If ``id`` is empty, values are non-finite, or ``fwhm`` is
            not positive.
    """

    id: str
    center: float
    fwhm: float
    area: float = 1.0

    def __post_init__(self) -> None:
        """Validate reflection identifiers and numeric fields."""
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("reflection id must be a non-empty string.")
        _finite_float(self.center, "reflection.center")
        fwhm_value = _finite_float(self.fwhm, "reflection.fwhm")
        _finite_float(self.area, "reflection.area")
        if fwhm_value <= 0.0:
            raise ValueError(f"reflection.fwhm must be positive, got {fwhm_value!r}.")


@dataclass(frozen=True)
class ReflectionBatch:
    """Deterministic group of reflections for profile execution.

    Args:
        index: Zero-based batch index.
        reflection_ids: Reflection identifiers in deterministic execution
            order.
        center_min: Minimum center in the batch.
        center_max: Maximum center in the batch.
    """

    index: int
    reflection_ids: tuple[str, ...]
    center_min: float
    center_max: float


def plan_reflection_batches(reflections: Sequence[Reflection], *, max_batch_size: int) -> list[ReflectionBatch]:
    """Create a deterministic reflection execution plan.

    Reflections are sorted by ``(center, id)`` before batching. This makes the
    output stable when callers pass reflections in different but equivalent
    orders.

    Args:
        reflections: Reflection records to batch.
        max_batch_size: Maximum number of reflections per batch. Must be
            positive.

    Returns:
        Ordered reflection batches.

    Raises:
        ValueError: If ``max_batch_size`` is not positive, reflection IDs are
            duplicated, or an item is not a :class:`Reflection`.

    Example:
        >>> plan_reflection_batches([Reflection("b", 2.0, 0.1), Reflection("a", 1.0, 0.1)], max_batch_size=1)[0].reflection_ids
        ('a',)
    """
    if isinstance(max_batch_size, bool) or not isinstance(max_batch_size, int) or max_batch_size <= 0:
        raise ValueError(f"max_batch_size must be a positive integer, got {max_batch_size!r}.")

    validated: list[Reflection] = []
    seen_ids: set[str] = set()
    for index, reflection in enumerate(reflections):
        if not isinstance(reflection, Reflection):
            raise ValueError(f"reflections[{index}] must be a Reflection.")
        if reflection.id in seen_ids:
            raise ValueError(f"Duplicate reflection id {reflection.id!r}.")
        seen_ids.add(reflection.id)
        validated.append(reflection)

    ordered = sorted(validated, key=lambda reflection: (reflection.center, reflection.id))
    batches: list[ReflectionBatch] = []
    for batch_index, start in enumerate(range(0, len(ordered), max_batch_size)):
        members = ordered[start : start + max_batch_size]
        batches.append(
            ReflectionBatch(
                index=batch_index,
                reflection_ids=tuple(member.id for member in members),
                center_min=members[0].center,
                center_max=members[-1].center,
            )
        )
    return batches


def _finite_sequence(values: Sequence[float], name: str) -> list[float]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    return [_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values)]


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _mixing_fraction(value: float, name: str) -> float:
    fraction = _finite_float(value, name)
    if not 0.0 <= fraction <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1, got {fraction!r}.")
    return fraction


def _clamp_unit_interval(value: float) -> float:
    return min(1.0, max(0.0, value))


def _require_sorted(values: Sequence[float], name: str) -> None:
    for index, (left, right) in enumerate(zip(values, values[1:], strict=False)):
        if right < left:
            raise ValueError(f"{name} must be sorted in non-decreasing order; item {index + 1} is out of order.")
