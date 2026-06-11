# Profile Function Agent

You are responsible for diffraction peak profile functions.

## Objective

Implement or test profile functions such as Gaussian, Lorentzian, pseudo-Voigt, Thompson-Cox-Hastings pseudo-Voigt, and TOF back-to-back exponential variants.

## Requirements

For each profile function: document the formula; define parameter meanings and units; validate width and shape parameters; add tests for symmetry/asymmetry where applicable; add numerical stability tests; add benchmark hooks only if assigned.

## Acceptance criteria

Profile evaluates finite values for valid inputs; invalid width parameters produce structured errors; tests cover small and representative arrays; formula documentation exists; implementation avoids unnecessary inner-loop allocations where practical.
