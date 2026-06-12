# AI Refinement Guide

## Purpose

This guide defines how AI-assisted refinement features must interact with
deterministic Rietveld Next tools.

## Scope

AI helpers may propose actions, call typed tool wrappers, log action metadata,
and produce reports. Numerical results must come from deterministic package
functions, not model text.

## Non-Goals

No autonomous mutation, hidden uncertainty suppression, or unverified numerical
claims are allowed. LLM calls are not part of the current foundation.

## Example

An AI tool wrapper should accept a typed request, call a deterministic helper,
record an action log entry, and return diagnostics that can be replayed or
reviewed by a human.

## Related Files

- [sections/09_ai_native_refinement.md](sections/09_ai_native_refinement.md)
- [validation_baseline.md](validation_baseline.md)
