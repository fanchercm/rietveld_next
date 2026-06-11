# Rust vs JAX Benchmark Agent

You are responsible for comparing Rust and JAX backend performance.

## Objective

Create a reproducible benchmark that compares equivalent Rust and JAX implementations of a simplified diffraction profile kernel.

## Benchmark kernel

`y_calc[x_i] = sum_j amplitude_j * exp(-0.5 * ((x_i - peak_position_j) / sigma_j)^2)`

## Required benchmark sizes

- small: 10,000 points, 100 peaks
- medium: 100,000 points, 1,000 peaks
- large: 1,000,000 points, 5,000 peaks

Large must be opt-in.

## Required outputs

JSON results, Markdown summary, checksum, dtype, backend, size, iterations, compile time where applicable, median/min/max runtime.

## Acceptance criteria

JAX compile time is separated from steady-state runtime; Rust timing is reported separately; small outputs match within tolerance when both are callable; missing JAX or Rust bindings are handled gracefully; documentation explains what the benchmark does and does not prove.
