# Part 11: Repository Architecture

```text
rietveld-next/
├── src/
│   ├── core/
│   │   ├── rn-core-rs/
│   │   ├── rn-schema/
│   │   └── rn-sdk-python/
│   ├── diffraction/
│   │   ├── symmetry/
│   │   ├── scattering/
│   │   ├── profiles/
│   │   ├── background/
│   │   └── corrections/
│   ├── xray/
│   │   ├── lab_cw/
│   │   ├── synchrotron_cw/
│   │   ├── pink_beam/
│   │   └── fpa/
│   ├── neutron/
│   │   ├── nuclear/
│   │   ├── magnetic/
│   │   ├── absorption/
│   │   ├── extinction/
│   │   └── mantid_adapters/
│   ├── tof/
│   │   ├── calibration/
│   │   ├── profiles/
│   │   ├── banks/
│   │   └── event_mode/
│   ├── edxrd/
│   │   ├── energy_calibration/
│   │   ├── detector_response/
│   │   ├── high_pressure/
│   │   └── workflows/
│   ├── optimization/
│   │   ├── local/
│   │   ├── global/
│   │   ├── bayesian/
│   │   ├── mcmc/
│   │   └── diagnostics/
│   ├── workflows/
│   │   ├── recipes/
│   │   ├── sequential/
│   │   ├── parametric/
│   │   ├── batch/
│   │   └── beamline/
│   ├── ai/
│   │   ├── agent/
│   │   ├── copilot/
│   │   ├── knowledge_base/
│   │   ├── tool_contracts/
│   │   └── evals/
│   ├── hpc/
│   │   ├── slurm/
│   │   ├── dask/
│   │   ├── ray/
│   │   ├── kubernetes/
│   │   └── result_store/
│   ├── desktop/
│   │   ├── tauri/
│   │   └── ui/
│   └── web/
│       ├── app/
│       ├── api/
│       └── visualization/
├── docs/
│   ├── theory/
│   ├── tutorials/
│   ├── api/
│   ├── developer/
│   └── validation/
├── backend_corpus/
│   └── manifests/
└── validation/
```

## 11.1 Package Boundaries

All implementation source code now lives under `src/`. Top-level directories
outside `src/` are reserved for documentation, schemas, prompts, backlog files,
GitHub import payloads, scaffold notes, validation planning, public backend
corpus fixtures, CI files, and project configuration. Top-level implementation
or test directories such as `core/`, `diffraction/`, `optimization/`,
`benchmarks/`, and `tests/` are forbidden.

- `src/rietveld_next/core`: domain model, parameter graph, provenance, schema.
- `src/rietveld_next/diffraction`: generic scattering, profiles, backgrounds, corrections.
- `src/rietveld_next/xray`: X-ray scattering, FPA, synchrotron and lab models.
- `src/rietveld_next/neutron`: nuclear scattering, absorption, magnetic structures, Mantid adapters.
- `src/rietveld_next/tof`: TOF calibration, bank models, event-mode hooks.
- `src/rietveld_next/edxrd`: energy calibration, detector response, high-pressure workflows.
- `src/rietveld_next/optimization`: local, global, Bayesian, and MCMC optimizers.
- `src/rietveld_next/workflows`: recipes, sequential, parametric, batch, beamline.
- `src/rietveld_next/ai`: agent, copilot, tool contracts, evals.
- `src/rietveld_next/hpc`: Slurm, Dask, Ray, Kubernetes, result store.
- `src/rietveld_next/desktop`: Tauri shell.
- `src/rietveld_next/web`: browser app and services.
