# ADR 0001: Use Rust for the Core Runtime

## Status

Proposed

## Context

The platform requires safe long-lived infrastructure, deterministic serialization, high concurrency, plugin boundaries, and deployment as both local and service components.

## Decision

Use Rust for the core domain model, parameter graph, provenance system, CPU production kernels, and service boundary.

## Consequences

Python bindings are required for scientific scripting. Some scientific contributors may need onboarding. High-performance C++/Kokkos kernels remain possible through plugin boundaries.
