# Rietveld Next Granular Milestones for Physics Calculation and Optimization

Total milestones: 40
Total mapped issues: 327

This milestone set expands the physics-calculation and optimization portions of the roadmap into finer work packages while preserving all issue mappings and the src/ layout guardrail.

## M01 Src-first architecture foundation

- Phase: Foundation
- Priority: P0
- Issues: #1, #2, #3, #4, #5, #6, #7, #8, #9, #10, #11, #12, #13, #14, #15
- Dependencies: None

### Scope
Establish the repository, source-layout guardrails, package boundaries, plugin capability model, and architecture decision workflow.

### Deliverables
- src-first monorepo scaffold
- workspace/build conventions
- package boundary document
- shared error taxonomy
- plugin capability model
- architecture decision record template

### Acceptance criteria
- [ ] Repository has no forbidden top-level implementation directories.
- [ ] Build and lint commands are documented.
- [ ] Package boundaries are explicit and enforceable.
- [ ] Architecture decision records can be created and reviewed.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M02 Core project model and schemas

- Phase: Foundation
- Priority: P0
- Issues: #16, #17, #18, #19, #20, #21, #22, #23, #24, #25, #26, #27, #28, #29, #30, #31, #32, #33, #34, #35
- Dependencies: M01

### Scope
Define typed project, experiment, dataset, histogram, phase, parameter, constraint, strategy, and sequential-study models.

### Deliverables
- core JSON schemas
- Rust/Python domain objects
- parameter ownership model
- constraint references
- schema round-trip tests

### Acceptance criteria
- [ ] All core entities serialize and deserialize deterministically.
- [ ] Schema validation rejects malformed project files.
- [ ] Parameter paths are stable and documented.
- [ ] Core model tests pass.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M03 Storage and data interchange foundation

- Phase: Foundation
- Priority: P0
- Issues: #36, #37, #38, #39, #40, #41, #42, #43, #44, #45, #46, #47, #48, #49, #50
- Dependencies: M02

### Scope
Create the project package, storage adapters, provenance log, and baseline data interchange paths.

### Deliverables
- project package layout
- JSONL provenance
- NeXus/HDF5 references
- Zarr/Parquet/Arrow adapter stubs
- import/export tests

### Acceptance criteria
- [ ] Project packages can be created, opened, and validated.
- [ ] Large array references are not embedded in JSON metadata.
- [ ] Provenance actions are append-only and replayable in tests.
- [ ] Storage documentation covers local and cloud usage.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M04 Residual objective and parameter transform foundation

- Phase: Physics and numerical engine
- Priority: P0
- Issues: #51, #52, #53, #63, #64, #65, #66
- Dependencies: M02

### Scope
Implement the residual-vector interface, parameter scaling, bounded transforms, objective registry, robust losses, and Poisson likelihood path.

### Deliverables
- residual vector API
- parameter scaling utilities
- bounded transforms
- objective registry
- robust loss functions
- Poisson likelihood objective

### Acceptance criteria
- [ ] Gaussian least-squares, robust, and Poisson objectives are selectable through a common interface.
- [ ] Invalid parameter values are handled through transforms or structured errors.
- [ ] Small synthetic objective tests verify residual shapes and values.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M05 Derivative and sparse Jacobian infrastructure

- Phase: Physics and numerical engine
- Priority: P0
- Issues: #54, #55, #56, #57, #69
- Dependencies: M04

### Scope
Implement sparse Jacobian structures, finite-difference fallback, analytic derivatives for scale/background parameters, and gradient test utilities.

### Deliverables
- sparse Jacobian data structure
- finite-difference derivative fallback
- analytic scale derivatives
- analytic background derivatives
- gradient verification utilities

### Acceptance criteria
- [ ] Sparse Jacobians preserve parameter-to-residual indexing.
- [ ] Analytic derivatives match finite differences within tolerance on synthetic cases.
- [ ] Gradient utilities produce actionable failure reports.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M06 Profile kernel and reflection batching foundation

- Phase: Physics calculation
- Priority: P0
- Issues: #58, #59, #60, #61, #62
- Dependencies: M04, M05

### Scope
Implement core peak-profile kernels and execution planning needed for efficient profile calculation.

### Deliverables
- Gaussian profile kernel
- pseudo-Voigt profile kernel
- Thompson-Cox-Hastings profile kernel
- peak window selection
- reflection batching plan

### Acceptance criteria
- [ ] Each profile kernel has numerical tests and documented parameter conventions.
- [ ] Peak windowing excludes negligible contributions without changing results beyond tolerance.
- [ ] Reflection batching produces deterministic execution plans.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M07 Uncertainty diagnostics and profile benchmark harness

- Phase: Physics and numerical engine
- Priority: P1
- Issues: #67, #68, #70
- Dependencies: M05, M06

### Scope
Implement covariance/correlation diagnostics and the first backend benchmark harness for profile calculations.

### Deliverables
- covariance calculation
- correlation matrix calculation
- profile backend benchmark harness

### Acceptance criteria
- [ ] Covariance and correlation outputs include parameter labels and units.
- [ ] Singular or ill-conditioned cases return warnings rather than misleading uncertainties.
- [ ] Benchmark results are machine-readable and reproducible.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M08 Local optimization adapters and rollback state

- Phase: Optimization
- Priority: P0
- Issues: #71, #72, #73, #74, #75
- Dependencies: M04, M05

### Scope
Implement local refinement infrastructure, including SciPy adapters, Rust optimizer trait, convergence reporting, and rollback snapshots.

### Deliverables
- trust-region adapter
- Levenberg-Marquardt adapter
- Rust optimizer trait
- convergence report object
- rollback snapshots

### Acceptance criteria
- [ ] A synthetic refinement runs through both local adapters where dependencies are available.
- [ ] Convergence reports include objective, iterations, termination reason, and parameter shifts.
- [ ] Rollback restores previous model state exactly.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M09 Global and multi-start optimization foundation

- Phase: Optimization
- Priority: P1
- Issues: #76, #77, #78, #79
- Dependencies: M08

### Scope
Implement initial global-search infrastructure for rugged refinement problems and autonomous starting-value discovery.

### Deliverables
- differential evolution adapter
- simulated annealing adapter
- multi-start runner
- Bayesian optimization placeholder API

### Acceptance criteria
- [ ] Global optimizers share a common result schema.
- [ ] Multi-start runs store seeds, candidates, objective values, and final local-refinement status.
- [ ] Expensive global tests are opt-in and excluded from normal CI.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M10 Probabilistic uncertainty and model comparison foundation

- Phase: Optimization
- Priority: P1
- Issues: #80, #81, #84, #85
- Dependencies: M08

### Scope
Add uncertainty and model-comparison APIs needed for scientific validation, publication-quality analysis, and autonomous model ranking.

### Deliverables
- MCMC uncertainty API
- optimizer result comparison utilities
- model-selection scoring interface
- reproducibility seed management

### Acceptance criteria
- [ ] MCMC API can run a minimal synthetic posterior example or clearly skip when backend dependencies are absent.
- [ ] Model-comparison outputs record objective, parameter count, likelihood assumptions, and warnings.
- [ ] Seed handling is deterministic and documented.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M11 Optimizer safeguard heuristics

- Phase: Optimization
- Priority: P1
- Issues: #82, #83
- Dependencies: M08, M10

### Scope
Implement parameter-freezing and overparameterization diagnostics that protect autonomous workflows from nonphysical or underdetermined refinements.

### Deliverables
- parameter-freezing heuristics
- overparameterization detector

### Acceptance criteria
- [ ] Highly correlated or unstable parameters are flagged with explanations.
- [ ] Heuristics produce recommendations rather than silently changing the model.
- [ ] Diagnostics are covered by synthetic pathological cases.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M12 Structural IO and symmetry baseline

- Phase: Physics calculation
- Priority: P0
- Issues: #86, #87, #88, #89
- Dependencies: M02

### Scope
Implement CIF ingestion, validation reporting, space-group lookup, and reflection generation.

### Deliverables
- CIF import v0
- CIF validation report
- space-group lookup service
- reflection generation service

### Acceptance criteria
- [ ] Representative CIFs import successfully.
- [ ] Validation reports identify missing/ambiguous crystallographic fields.
- [ ] Reflection generation matches reference cases for simple space groups.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M13 Scattering factors and basic corrections

- Phase: Physics calculation
- Priority: P0
- Issues: #90, #91, #92, #93
- Dependencies: M12

### Scope
Implement scattering tables and first-pass diffraction corrections needed by X-ray and neutron calculations.

### Deliverables
- X-ray form factor table
- neutron scattering length table
- multiplicity calculation
- Lorentz-polarization correction

### Acceptance criteria
- [ ] Scattering tables include citation/provenance metadata.
- [ ] Multiplicity and Lorentz-polarization tests match reference calculations.
- [ ] X-ray and neutron scattering lookup APIs are radiation-specific.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M14 Orientation, microstructure, and background models

- Phase: Physics calculation
- Priority: P1
- Issues: #94, #95, #96, #97, #98
- Dependencies: M06, M13

### Scope
Implement first-generation preferred-orientation, size/strain broadening, and polynomial/Chebyshev background models.

### Deliverables
- preferred orientation model v0
- isotropic size broadening
- isotropic strain broadening
- polynomial background model
- Chebyshev background model

### Acceptance criteria
- [ ] Each model has parameter bounds and validation rules.
- [ ] Background models can be refined independently from phase/profile parameters.
- [ ] Size and strain contributions are separately testable on synthetic patterns.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M15 Synthetic patterns, phase scales, and structural validation

- Phase: Physics calculation
- Priority: P1
- Issues: #99, #100, #101, #102, #103, #104, #105
- Dependencies: M12, M13, M14

### Scope
Create end-to-end synthetic pattern generation and phase quantification support with structural validation checks.

### Deliverables
- reflection tick generation
- synthetic pattern generator
- standard reference dataset registry
- phase scale model
- phase fraction calculation
- occupancy constraints
- ADP validation checks

### Acceptance criteria
- [ ] Synthetic patterns include phase ticks and metadata.
- [ ] Phase fraction calculation documents assumptions and normalization.
- [ ] Occupancy and ADP validation produce structured warnings.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M16 Lab and synchrotron CW X-ray instrument baseline

- Phase: Physics calculation
- Priority: P1
- Issues: #106, #107, #108, #109, #115
- Dependencies: M13, M15

### Scope
Implement lab and synchrotron CW X-ray instrument models and basic calibration/metadata validation workflows.

### Deliverables
- lab CW XRD instrument model
- synchrotron CW XRD instrument model
- wavelength metadata validation
- zero-shift calibration workflow
- beamline metadata template

### Acceptance criteria
- [ ] Instrument models distinguish lab and synchrotron metadata.
- [ ] Zero-shift calibration is reproducible on a synthetic/reference case.
- [ ] Missing wavelength or beamline metadata produces actionable validation messages.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M17 Fundamental-parameters and detector hook foundation

- Phase: Physics calculation
- Priority: P2
- Issues: #110, #111, #112, #113, #114
- Dependencies: M16

### Scope
Create extensible APIs for fundamental-parameters, emission spectra, axial divergence, detector resolution, and 2D integration metadata links.

### Deliverables
- fundamental-parameters API skeleton
- emission spectrum model skeleton
- axial divergence hook
- detector resolution hook
- 2D integration metadata link

### Acceptance criteria
- [ ] Hooks are registered through the plugin/capability system.
- [ ] Skeleton implementations are documented as incomplete physics models.
- [ ] Tests verify that instrument hooks compose with the profile evaluation path.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M18 CW neutron instrument and correction physics

- Phase: Physics calculation
- Priority: P1
- Issues: #116, #117, #118, #119, #120
- Dependencies: M13, M15

### Scope
Implement CW neutron instrument modeling, isotope scattering lookup, absorption hooks, sample geometry corrections, and extinction interfaces.

### Deliverables
- CW neutron instrument model
- isotope scattering-length lookup
- wavelength-dependent absorption hooks
- sample geometry correction interface
- extinction correction interface

### Acceptance criteria
- [ ] Neutron instrument models use neutron scattering lengths rather than X-ray form factors.
- [ ] Absorption/extinction interfaces can be attached without changing core profile kernels.
- [ ] Reference neutron calculations pass baseline validation.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M19 Neutron data integration and joint weighting

- Phase: Physics calculation
- Priority: P1
- Issues: #121, #122, #123, #124, #125
- Dependencies: M18

### Scope
Implement neutron-specific background, joint weighting, Mantid import, and uncertainty checks.

### Deliverables
- container background model
- neutron joint weighting model
- nuclear neutron validation example
- Mantid reduced-data import adapter
- neutron uncertainty model checks

### Acceptance criteria
- [ ] Mantid reduced-data import handles at least one documented example shape.
- [ ] Joint weighting records likelihood/weighting assumptions.
- [ ] Validation example can be run from documentation.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M20 TOF data model, calibration, and masks

- Phase: Physics calculation
- Priority: P1
- Issues: #126, #127, #128, #129, #140
- Dependencies: M18

### Scope
Implement TOF histogram axis, detector bank model, calibration parameter set, DIFC/DIFA/zero peak positions, and bank masks.

### Deliverables
- TOF histogram axis model
- TOF detector bank entity
- TOF calibration parameter set
- DIFC-DIFA-zero peak position model
- TOF bank mask handling

### Acceptance criteria
- [ ] Multi-bank projects can represent independent bank calibration parameters.
- [ ] Peak-position tests cover at least two banks.
- [ ] Bank masks propagate into residual calculation.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M21 TOF bank profile and multi-bank objective

- Phase: Physics calculation
- Priority: P1
- Issues: #130, #131, #132, #133, #134
- Dependencies: M20, M06

### Scope
Implement bank-specific backgrounds, profile parameters, back-to-back exponential profiles, TOF windowing, and multi-bank objective assembly.

### Deliverables
- bank-specific background model
- bank-specific profile parameter model
- back-to-back exponential profile
- TOF reflection windowing
- multi-bank objective assembly

### Acceptance criteria
- [ ] Each bank can refine local profile/background parameters while sharing phase parameters.
- [ ] Back-to-back exponential tests verify asymmetry and normalization behavior.
- [ ] Multi-bank objective returns labeled residual blocks.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M22 TOF validation diagnostics and workflow specs

- Phase: Physics calculation
- Priority: P2
- Issues: #135, #136, #137, #138, #139
- Dependencies: M20, M21

### Scope
Add TOF benchmarks, calibration workflow specification, diagnostics, event-mode provenance placeholder, and GSAS-II comparison fixture.

### Deliverables
- TOF synthetic benchmark
- TOF calibration wizard spec
- TOF diagnostic plot data
- event-mode provenance placeholder
- GSAS-II TOF comparison fixture

### Acceptance criteria
- [ ] TOF benchmark is reproducible and not run in expensive mode by default.
- [ ] Calibration wizard spec maps GUI steps to API calls.
- [ ] Comparison fixture documents expected tolerances and limitations.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M23 Magnetic entities and magnetic scattering foundation

- Phase: Physics calculation
- Priority: P1
- Issues: #141, #142, #143
- Dependencies: M13, M18

### Scope
Introduce magnetic moment, propagation-vector, and magnetic form-factor entities.

### Deliverables
- magnetic moment entity
- propagation vector entity
- magnetic form-factor table

### Acceptance criteria
- [ ] Magnetic entities are serializable in the core model.
- [ ] Magnetic form-factor lookup includes provenance metadata.
- [ ] Basic validation catches invalid moment definitions.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M24 Magnetic symmetry and import foundation

- Phase: Physics calculation
- Priority: P2
- Issues: #144, #145, #146
- Dependencies: M23

### Scope
Create mCIF import skeleton, magnetic symmetry constraint API, and representation-analysis import placeholder.

### Deliverables
- mCIF import skeleton
- magnetic symmetry constraint API
- representation-analysis import placeholder

### Acceptance criteria
- [ ] mCIF import clearly reports supported and unsupported fields.
- [ ] Magnetic symmetry constraints are represented in the parameter graph.
- [ ] Representation-analysis placeholder includes documented extension contract.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M25 Magnetic joint-refinement validation and recipes

- Phase: Physics calculation
- Priority: P2
- Issues: #147, #148, #149, #150, #151, #152
- Dependencies: M23, M24, M19

### Scope
Implement nuclear-plus-magnetic coupling, magnetic reflection handling, validation, reports, and refinement recipes.

### Deliverables
- nuclear-plus-magnetic phase coupling
- magnetic reflection flagging
- moment magnitude validation
- tutorial dataset stub
- magnetic report section generator
- magnetic parameter group recipes

### Acceptance criteria
- [ ] Magnetic and nuclear contributions can be toggled and reported separately.
- [ ] Moment magnitude validation produces scientific warnings.
- [ ] Recipe docs explain safe staged magnetic refinement.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M26 EDXRD axis and calibration foundation

- Phase: Physics calculation
- Priority: P2
- Issues: #153, #154, #155, #164, #166
- Dependencies: M13, M15

### Scope
Implement energy-axis histograms, channel-to-energy calibration, fixed-angle Bragg conversion, EDXRD calibration workflow, and import template.

### Deliverables
- energy-axis histogram model
- channel-to-energy calibration polynomial
- fixed-angle Bragg conversion
- EDXRD calibration workflow
- EDXRD import template

### Acceptance criteria
- [ ] Energy-axis data can be represented without lossy conversion to 2theta.
- [ ] Calibration workflow stores coefficients and provenance.
- [ ] Fixed-angle conversion tests cover known standards.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M27 EDXRD detector response and correction hooks

- Phase: Physics calculation
- Priority: P2
- Issues: #156, #157, #158, #159, #160
- Dependencies: M26, M06

### Scope
Implement the EDXRD detector response API, Gaussian response kernel, tail/escape hooks, and dead-time metadata.

### Deliverables
- detector response API
- Gaussian detector response kernel
- low-energy tail response hook
- escape peak correction hook
- dead-time correction metadata

### Acceptance criteria
- [ ] Detector response kernels are separable from crystallographic peak generation.
- [ ] Correction hooks are optional and provenance-recorded.
- [ ] Tests document current physical limitations.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M28 EDXRD high-pressure validation and documentation

- Phase: Physics calculation
- Priority: P2
- Issues: #161, #162, #163, #165, #167
- Dependencies: M26, M27

### Scope
Add high-pressure entities, equation-of-state hook, synthetic benchmark, residual diagnostics, and user documentation example.

### Deliverables
- high-pressure marker entity
- equation-of-state hook
- EDXRD synthetic benchmark
- EDXRD residual diagnostics
- EDXRD documentation example

### Acceptance criteria
- [ ] High-pressure marker metadata is represented in the project model.
- [ ] EDXRD benchmark writes reproducible results.
- [ ] Documentation walks through calibration and refinement assumptions.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M29 Sequential and parametric workflow foundation

- Status: Closed
- Closed: 2026-06-11
- Closed by: Batch E subagent execution
- Phase: Workflow
- Priority: P1
- Issues: #168, #169, #170, #171, #172, #173, #174, #175, #176, #177, #178, #179, #180, #181, #182
- Dependencies: M15, M08

### Scope
Implement sequential/parametric study execution, parameter evolution tables, and recipe plumbing.

### Deliverables
- sequential runner
- parametric model API
- batch recipe integration
- study result tables
- workflow validation examples

### Acceptance criteria
- [x] Sequential studies run deterministically on synthetic series.
- [x] Parameter evolution tables include units, uncertainties, and provenance.
- [x] Workflow recipes are scriptable and replayable.

### Definition of done
- [x] All mapped issues are closed or explicitly deferred with rationale.
- [x] All implementation source created by this milestone is under src/.
- [x] Public APIs, schemas, and generated artifacts are documented.
- [x] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [x] Codex-facing notes include commands to reproduce validation or benchmark results.

### Closure evidence
- `docs/batch_e_completion_report.md`

### Closure validation
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next -p test*.py`

## M30 AI tool-grounded refinement foundation

- Status: Closed
- Closed: 2026-06-11
- Closed by: Batch E subagent execution
- Phase: AI
- Priority: P1
- Issues: #183, #184, #185, #186, #187, #188, #189, #190, #191, #192, #193, #194, #195, #196, #197, #198, #199, #200, #201, #202
- Dependencies: M08, M11, M29

### Scope
Implement deterministic tool contracts, agent diagnostics, rollback-aware planning, and AI evaluation scaffolding.

### Deliverables
- AI tool schemas
- diagnostic tools
- agent action logs
- strategy rules
- AI evaluation tasks

### Acceptance criteria
- [x] Every AI action maps to a deterministic tool call.
- [x] Agent logs are replayable without the LLM.
- [x] Safety tests cover nonphysical and overfitting scenarios.

### Definition of done
- [x] All mapped issues are closed or explicitly deferred with rationale.
- [x] All implementation source created by this milestone is under src/.
- [x] Public APIs, schemas, and generated artifacts are documented.
- [x] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [x] Codex-facing notes include commands to reproduce validation or benchmark results.

### Closure evidence
- `docs/batch_e_completion_report.md`

### Closure validation
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next -p test*.py`

## M31 Desktop and web UX foundation

- Status: Closed
- Closed: 2026-06-11
- Closed by: Batch E subagent execution
- Phase: UX
- Priority: P1
- Issues: #203, #204, #205, #206, #207, #208, #209, #210, #211, #212, #213, #214, #215, #216, #217, #218, #219, #220, #221, #222
- Dependencies: M01, M02, M08

### Scope
Build the first desktop/web user experience for import, visualization, parameter editing, guided workflows, and reports.

### Deliverables
- desktop shell
- web app skeleton
- pattern viewer
- parameter table
- guided workflow screens
- report export

### Acceptance criteria
- [x] Core workflows are accessible from GUI and script API.
- [x] GUI actions emit provenance events.
- [x] UX tests cover import-through-simple-refinement path.

### Definition of done
- [x] All mapped issues are closed or explicitly deferred with rationale.
- [x] All implementation source created by this milestone is under src/.
- [x] Public APIs, schemas, and generated artifacts are documented.
- [x] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [x] Codex-facing notes include commands to reproduce validation or benchmark results.

### Closure evidence
- `docs/batch_e_completion_report.md`

### Closure validation
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next -p test*.py`

## M32 Visualization and diagnostics foundation

- Status: Closed
- Closed: 2026-06-11
- Closed by: Batch E subagent execution
- Phase: UX
- Priority: P1
- Issues: #223, #224, #225, #226, #227, #228, #229, #230, #231, #232
- Dependencies: M07, M29

### Scope
Implement core visual diagnostics for profiles, correlations, residuals, sequential studies, and parameter graphs.

### Deliverables
- profile plots
- correlation heatmap
- residual diagnostics
- parameter graph visualization
- sequential dashboards

### Acceptance criteria
- [x] Visual data payloads are testable without rendering.
- [x] Plots distinguish observed, calculated, difference, and phase ticks.
- [x] Correlation and residual warnings are linked to parameters.

### Definition of done
- [x] All mapped issues are closed or explicitly deferred with rationale.
- [x] All implementation source created by this milestone is under src/.
- [x] Public APIs, schemas, and generated artifacts are documented.
- [x] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [x] Codex-facing notes include commands to reproduce validation or benchmark results.

### Closure evidence
- `docs/batch_e_completion_report.md`

### Closure validation
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next -p test*.py`

## M33 HPC and cloud execution foundation

- Status: Closed
- Closed: 2026-06-11
- Closed by: Batch E subagent execution
- Phase: HPC
- Priority: P1
- Issues: #233, #234, #235, #236, #237, #238, #239, #240, #241, #242, #243, #244, #245, #246, #247
- Dependencies: M29

### Scope
Implement local, Slurm, Dask/Ray, Kubernetes, and result-store execution foundations.

### Deliverables
- local batch runner
- Slurm adapter
- Dask adapter
- Ray adapter
- Kubernetes worker prototype
- result store

### Acceptance criteria
- [x] Local batch execution handles synthetic ensembles.
- [x] Scheduler adapters have fake/local tests.
- [x] Result records are reproducible and portable.

### Definition of done
- [x] All mapped issues are closed or explicitly deferred with rationale.
- [x] All implementation source created by this milestone is under src/.
- [x] Public APIs, schemas, and generated artifacts are documented.
- [x] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [x] Codex-facing notes include commands to reproduce validation or benchmark results.

### Closure evidence
- `docs/batch_e_completion_report.md`

### Closure validation
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s src/rietveld_next -p test*.py`

## M34 Validation and testing baseline

- Phase: Quality
- Priority: P0
- Issues: #248, #249, #250, #251, #252, #253, #254, #255, #256, #257, #258, #259, #260, #261, #262, #263, #264, #265, #266, #267
- Dependencies: M03, M15, M19, M22

### Scope
Establish scientific validation, golden regression tests, CI gates, and numerical tolerance policies.

### Deliverables
- unit/integration tests
- golden scientific cases
- optimizer regression suite
- cross-platform CI
- validation report generator

### Acceptance criteria
- [ ] Validation tests run in CI with documented tolerances.
- [ ] Expensive tests are clearly marked.
- [ ] Validation report summarizes pass/fail and known limitations.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M35 Documentation and governance baseline

- Phase: Governance
- Priority: P1
- Issues: #268, #269, #270, #271, #272, #273, #274, #275, #276, #277, #278, #279, #280, #281, #282, #283, #284, #285, #286, #287
- Dependencies: M01, M34

### Scope
Create user, developer, theory, governance, citation, and reproducibility documentation.

### Deliverables
- theory guide
- beginner tutorial
- developer guide
- plugin guide
- governance docs
- citation guide

### Acceptance criteria
- [ ] Docs build successfully.
- [ ] Tutorials reference tested examples.
- [ ] Governance and contribution policies are explicit.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M36 Benchmarking foundation and result infrastructure

- Phase: Benchmarking
- Priority: P1
- Issues: #288, #289, #290, #291, #292, #293, #294, #295
- Dependencies: M07

### Scope
Define benchmark taxonomy, result schemas, backend comparison harnesses, and initial profile benchmark workflow.

### Deliverables
- benchmark taxonomy
- JSON result schema
- Rust/JAX benchmark harness
- profile benchmark docs

### Acceptance criteria
- [ ] Benchmarks write machine-readable results.
- [ ] Compile time and steady-state time are separated.
- [ ] Large benchmarks are opt-in.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M37 Numerical and optimization benchmark suite

- Phase: Benchmarking
- Priority: P1
- Issues: #296, #297, #298, #299, #300, #301, #302, #303
- Dependencies: M08, M09

### Scope
Benchmark profile kernels, sparse Jacobians, AD, local optimizers, global optimizers, and uncertainty APIs.

### Deliverables
- pseudo-Voigt benchmark
- Jacobian benchmark
- AD benchmark
- optimizer benchmark
- global search benchmark

### Acceptance criteria
- [ ] Benchmark outputs include size, backend, dtype, iterations, timings, and checksum.
- [ ] Baseline results are reproducible.
- [ ] Benchmark tests avoid expensive defaults.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M38 Physics workflow benchmark suite

- Phase: Benchmarking
- Priority: P1
- Issues: #304, #305, #306, #307, #308, #309, #310, #311
- Dependencies: M21, M25, M28, M29

### Scope
Benchmark sequential, parametric, batch, TOF, neutron, magnetic, and EDXRD workflows.

### Deliverables
- sequential benchmark
- parametric benchmark
- TOF benchmark
- magnetic benchmark
- EDXRD benchmark

### Acceptance criteria
- [ ] Each benchmark documents scientific assumptions.
- [ ] Workflow benchmarks produce result tables and diagnostics.
- [ ] Benchmarks are usable for regression tracking.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M39 Storage, diagnostics, visualization, AI, and HPC benchmark suite

- Phase: Benchmarking
- Priority: P2
- Issues: #312, #313, #314, #315, #316, #317, #318, #319, #320
- Dependencies: M30, M32, M33

### Scope
Benchmark storage backends, visualization payloads, diagnostics, AI-agent loops, schedulers, and distributed execution.

### Deliverables
- storage benchmark
- diagnostics benchmark
- visualization benchmark
- AI loop benchmark
- scheduler benchmark

### Acceptance criteria
- [ ] Benchmarks produce comparable JSON artifacts.
- [ ] Scheduler benchmarks can run locally with fake adapters.
- [ ] AI benchmarks do not depend on nondeterministic LLM output for pass/fail.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.

## M40 Benchmark regression, dashboard, and CI integration

- Phase: Benchmarking
- Priority: P1
- Issues: #321, #322, #323, #324, #325, #326, #327
- Dependencies: M36, M37, M38, M39

### Scope
Integrate benchmark baselines, dashboards, regression thresholds, CI smoke benchmarks, and documentation.

### Deliverables
- benchmark baseline registry
- dashboard artifact
- performance regression thresholds
- CI smoke benchmark
- benchmark documentation

### Acceptance criteria
- [ ] CI runs lightweight benchmarks only.
- [ ] Regression thresholds are explicit and reviewable.
- [ ] Dashboard artifacts can be regenerated from JSON results.

### Definition of done
- [ ] All mapped issues are closed or explicitly deferred with rationale.
- [ ] All implementation source created by this milestone is under src/.
- [ ] Public APIs, schemas, and generated artifacts are documented.
- [ ] Unit, integration, or validation tests relevant to the milestone pass in CI.
- [ ] Codex-facing notes include commands to reproduce validation or benchmark results.
