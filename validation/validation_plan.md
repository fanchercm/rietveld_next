# Scientific Validation and Benchmark Plan

## Validation tiers

1. Synthetic analytical tests: known parameters are recovered within tolerance.
2. Golden-pattern tests: fixed datasets produce stable outputs across commits.
3. Cross-software comparisons: compare against GSAS-II, FullProf, MAUD, and TOPAS where permitted.
4. Facility datasets: neutron TOF, CW neutron, synchrotron XRD, EDXRD, and joint X-ray/neutron examples.
5. Stress tests: poor starting values, missing phases, overfitting traps, high correlations, low-count data.

## Required metrics

- Rwp, Rp, chi-square, and log-likelihood where applicable.
- Parameter values and uncertainties.
- Correlation matrix.
- Residual diagnostics by region, bank, phase, and sequential coordinate.
- Runtime and memory.
- Reproducibility checksum.

## Release gate

A scientific feature cannot be marked production-ready until it passes synthetic tests, golden regression tests, documentation review, and at least one domain-expert review for the relevant diffraction modality.
