# Plugin Developer Guide

## Purpose

This guide explains how plugin-like extensions should declare capabilities
without bypassing core package boundaries.

## Scope

Plugins should describe supported radiation types, axes, parameters, units,
validation functions, and API stability. The current capability model is
metadata-only.

## Non-Goals

Plugins must not introduce parallel model graphs, hidden numerical kernels, or
top-level implementation directories.

## Example

Declare a capability through the architecture foundation model, include units
for every parameter, and add package-local tests that verify invalid capability
metadata fails clearly.

## Related Files

- [plugin_capability_model.md](plugin_capability_model.md)
- [PACKAGE_TREE.md](PACKAGE_TREE.md)
