# ADR 0003: Tool-Grounded AI Only

## Status

Proposed

## Decision

LLM agents may recommend strategy, explain results, and call tools. Numerical results and model mutations must come from deterministic APIs that produce provenance events.

## Consequences

Agent behavior can be audited, replayed, evaluated, and constrained. Free-form LLM output is never considered a scientific result.
