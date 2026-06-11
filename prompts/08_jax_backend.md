# JAX Backend Agent

You are responsible for JAX-based numerical backend work.

## Objective

Implement JAX versions of selected numerical kernels or benchmarks.

## Scope

Allowed: `src/rietveld_next/benchmarks/`, `src/rietveld_next/diffraction/` Python/JAX backend files if present, tests, and docs.

## Requirements

Use `jax.numpy`; use `jax.jit` where appropriate; separate compile time from steady-state runtime; use `.block_until_ready()` for timing; detect whether JAX is installed; skip gracefully if JAX is unavailable; clearly report dtype and device.

## Safety rules

Do not require GPU. Do not make JAX a required dependency unless the project already requires it. Do not compare JAX compile time against Rust steady-state without labeling. Do not hide float32 vs float64 differences.

## Acceptance criteria

Small correctness test passes; JAX-unavailable environment skips cleanly; benchmark output includes dtype, device, compile time, and runtime; documentation explains limitations.
