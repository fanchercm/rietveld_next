# Executive Thesis

The next major Rietveld platform should not be a prettier clone of GSAS-II, FullProf, TOPAS, MAUD, or Mantid-based workflows. It should be a scientific operating system for diffraction refinement: a reproducible model graph, differentiable numerical engine, instrument-aware data model, autonomous strategy layer, and modern interactive UX that can run locally, at beamlines, on HPC clusters, and in cloud-native high-throughput environments.

The central design principle is:

> Separate scientific model semantics from numerical kernels, workflow orchestration, user interface, and AI strategy.

Existing systems prove that each capability is possible. GSAS-II demonstrates breadth, scripting, and joint X-ray/neutron workflows; FullProf demonstrates magnetic and neutron maturity; TOPAS demonstrates an elegant constraint and computer-algebra refinement architecture; MAUD demonstrates combined texture and microstructure analysis; Mantid demonstrates neutron facility data reduction at scale; Spotlight and Rongzai show the direction of HPC- and AI-assisted refinement. The opportunity is to combine these lessons into a modular, auditable, high-performance platform rather than another monolithic desktop application.

The proposed system, referred to here as **Rietveld Next**, should be:

- **Schema-first**: every project, parameter, constraint, histogram, instrument, and action has a typed representation.
- **API-first**: every GUI action is scriptable and every script action is visible in the GUI.
- **Instrument-aware**: CW XRD, synchrotron XRD, EDXRD, CW neutron, TOF neutron, and multi-bank instruments are first-class models.
- **Refinement-graph based**: parameters are nodes in a dependency graph rather than opaque entries in a flat table.
- **HPC-capable**: local desktop, workstation, Slurm clusters, Dask/Ray workflows, and Kubernetes deployments use the same model semantics.
- **AI-native but physics-grounded**: LLM agents may recommend strategies and explain results, but deterministic physics engines produce the numerical results.
