# Part 7: Energy Dispersive Diffraction

## 7.1 Physical Model

In EDXRD, detector angle is usually fixed and the diffraction condition is scanned in photon energy:

$$
d = \frac{hc}{2E\sin\theta}
$$

The model must operate directly on energy $E$, not merely convert data to d-spacing and use CW machinery blindly.

## 7.2 EDXRD Profile Model

A correct EDXRD engine needs:

- Energy calibration: $E(c)=a_0+a_1c+a_2c^2+\cdots$.
- Detector response: Gaussian core, low-energy tailing, escape peaks, pile-up, dead-time correction, and nonlinearity.
- Incident spectrum: white-beam spectral intensity, absorption edges, source decay, and normalization.
- Energy-dependent absorption: sample, pressure cell, gasket, windows, and environment.
- Fixed-angle geometry and uncertainty.
- High-pressure calibration: standard material, pressure marker, and equation-of-state integration.
- In situ time-series support.

## 7.3 Software Recommendations

1. Add `axis = energy` as a first-class histogram type.
2. Define an `EnergyDispersiveInstrument` subclass.
3. Implement detector response plugins.
4. Implement channel-to-energy, angle, standard-material, and pressure-marker calibration workflows.
5. Support mixed EDXRD + angle-dispersive refinement.
6. Preserve raw spectra and correction provenance.
7. Provide high-pressure UX templates.
