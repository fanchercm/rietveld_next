# Rust Backend Benchmark Agent

You are responsible for Rust numerical performance benchmarks.

## Objective

Implement Rust-side benchmark support for representative profile calculations.

## Scope

Allowed: Rust numerical packages under `src/`, benchmark harnesses under `src/rietveld_next/benchmarks/` or existing project benchmark location, docs/tests.

## Requirements

Use deterministic synthetic data; report median/min/max runtime; include checksum; avoid expensive benchmarks in normal CI; use safe Rust unless an unsafe block is explicitly justified and reviewed; keep benchmark output machine-readable.

## Acceptance criteria

Rust benchmark runs from a documented command; JSON result output is produced or compatible with the shared benchmark schema; small correctness test is included; large benchmark is opt-in.
