# Part 2: Competitive Software Landscape

## 2.1 Open Source and Academic Systems

### GSAS

GSAS established the comprehensive phase/histogram paradigm and remains historically important. It is scientifically broad but architecturally legacy. Its main lesson is that a durable Rietveld platform must support multiple experiments, multiple phases, and shared constraints across them.

### GSAS-II

GSAS-II is the strongest open-source all-purpose baseline. It supports powder and single-crystal workflows, X-ray and neutron data, CW and TOF, sequential refinement, joint refinement, PDF tools, image integration, and scripting. Its Python interface is the closest existing model for a scriptable refinement application.

**Strengths:** broad capability, active open-source development, tutorials, scripting, and joint refinement.

**Limitations:** GUI-centered project tree and internal data structures are not ideal as a future HPC/cloud/AI-native kernel.

**Lesson:** Use GSAS-II for scientific validation and interoperability while designing cleaner typed APIs.

### FullProf

FullProf remains the magnetic and neutron reference system. It supports CW and TOF neutron diffraction, X-ray diffraction, magnetic structures, propagation vectors, profile matching, preferred orientation, microstructure, absorption, and mixed neutron/X-ray refinement.

**Strengths:** expert magnetic/neutron power.

**Limitations:** steep learning curve and text-driven control files.

**Lesson:** Match FullProf's scientific depth while replacing control-file fragility with model graphs and interactive validation.

### MAUD

MAUD is the key reference for texture, microstructure, residual stress, and combined analysis.

**Strengths:** combined texture/microstructure/materials analysis.

**Limitations:** aging Java desktop UX and less modern automation/HPC design.

**Lesson:** Include texture and microstructure as core domain models.

### Profex/BGMN

Profex provides a graphical workflow around BGMN and is strong for routine quantitative phase analysis.

**Strengths:** practical UX for routine XRD and batch work.

**Limitations:** less advanced neutron/magnetic/TOF scope.

**Lesson:** Routine workflows need guided defaults and templates.

### Mantid

Mantid is a facility-scale neutron and muon data reduction and analysis framework, not primarily a Rietveld platform. It is crucial for reduction, event data, instrument definitions, and neutron facility integration.

**Lesson:** Integrate with Mantid; do not duplicate all neutron reduction infrastructure.

### Jana2006 and Jana2020

Jana is important for advanced crystallography, modulated structures, superspace, and magnetic structures.

**Lesson:** The symmetry layer must be powerful enough for magnetic and superspace structures.

### ReX, oneXRD, Spotlight, FullProfAPP

- **ReX:** useful precedent for accessible Rietveld workflows, but not the full scientific ceiling.
- **oneXRD:** modern Python plugin architecture and GSAS-II integration; instructive for modular UX.
- **Spotlight:** high-throughput/HPC global optimization layer; crucial precedent for autonomous robust refinement.
- **FullProfAPP:** demonstrates modern automation UX around FullProf.

## 2.2 Commercial Systems

### TOPAS

TOPAS is the strongest architectural reference for constraint-rich refinement. It combines C++ numerical performance, a powerful scripting language, computer algebra, derivative/dependency management, restraints, penalties, bounds, simulated annealing, and fundamental-parameters modeling.

**Lesson:** A new platform needs TOPAS-like expression power but open, typed, testable, and scriptable semantics.

### HighScore Plus, Jade, Match!

These systems are strong for routine phase identification, quantitative analysis, reporting, and industrial workflows. Their advantages are polish, databases, and guided workflows. Their limitations are closed ecosystems and less transparent extensibility.

**Lesson:** Beginner workflows, database integration, and report generation matter as much as numerical power.

## 2.3 Emerging AI Systems

### Rongzai Agent

Rongzai demonstrates LLM-assisted autonomous neutron refinement using a tool loop around GSAS-II, expert knowledge, diagnostics, rollback, and report generation.

**Lesson:** AI should orchestrate deterministic tools and produce auditable action logs.

### Autonomous GSAS-II Workflows

GSAS-II scripting enables automation and high-throughput workflows. This validates API-first design.

### Spotlight

Spotlight uses HPC-scale sampling, local optimization, and surrogate models to make high-throughput refinement more robust against bad starting points and local minima.

**Lesson:** Global search and result databases should be first-class services.

## 2.4 Scientific Feature Matrix

Legend: strong/native = `++`, supported = `+`, partial/external = `~`, not primary/unclear = `-`. The table is grouped into compact feature families so it remains usable in both Markdown and PDF.

| Package | Core diffraction modes | Advanced science | Workflow, joint refinement, and automation |
|---|---|---|---|
| GSAS | CW XRD `++`; synchrotron XRD `+`; EDXRD `~`; CW neutron `++`; TOF neutron `++` | magnetic `+`; texture `~`; microstructure `+`; PDF `-` | sequential `~`; joint `++`; batch/API `~`; automation `~` |
| GSAS-II | CW XRD `++`; synchrotron XRD `++`; EDXRD `~/+`; CW neutron `++`; TOF neutron `++` | magnetic `+`; texture `+`; microstructure `+`; PDF `+` | sequential `++`; joint `++`; batch/API `++`; automation `+` |
| FullProf | CW XRD `++`; synchrotron XRD `++`; EDXRD `+`; CW neutron `++`; TOF neutron `++` | magnetic `++`; texture `+`; microstructure `+`; PDF `~` | sequential `+`; joint `++`; batch/API `~`; automation `~` |
| MAUD | CW XRD `++`; synchrotron XRD `++`; EDXRD `~`; CW neutron `+`; TOF neutron `+` | magnetic `~`; texture `++`; microstructure `++`; PDF `~` | sequential `+`; joint `+`; batch/API `~`; automation `~` |
| Profex/BGMN | CW XRD `++`; synchrotron XRD `+`; EDXRD `~`; CW neutron `~`; TOF neutron `-` | magnetic `-`; texture `~`; microstructure `+`; PDF `-` | sequential `+`; joint `~`; batch/API `+`; automation `+` |
| Mantid | XRD `~`; neutron reduction `++`; TOF reduction `++`; total scattering reduction `++` | magnetic `~`; texture `~`; microstructure `~`; PDF/total scattering `++` | sequential `+`; joint `~`; Python API `++`; automation `+` |
| Jana2020 | CW XRD `+`; synchrotron XRD `+`; CW neutron `+`; TOF neutron `~` | magnetic `++`; superspace/modulated structures `++`; texture `~`; microstructure `~` | sequential `~`; joint `+`; batch/API `~`; automation `~` |
| oneXRD | CW XRD `++`; synchrotron XRD `+`; neutron/TOF via plugins | magnetic via GSAS-II plugin; texture `~`; microstructure `+`; PDF `-` | sequential `+`; joint `~`; batch/API `+`; automation `+` |
| Spotlight | Engine-dependent modalities | Engine-dependent scientific models | sequential/high-throughput `++`; batch/API `++`; automation `++`; global search `++` |
| TOPAS | CW XRD `++`; synchrotron XRD `++`; EDXRD `~/+`; CW neutron `+`; TOF neutron `+` | magnetic `~/+`; texture `+`; microstructure `++`; PDF `+` | sequential `++`; joint `++`; batch/API `++`; automation `+` |
| HighScore Plus | CW XRD `++`; synchrotron XRD `+`; neutron `~` | texture `~`; microstructure `+`; PDF `~`; magnetic `-` | sequential `+`; joint `~`; batch/API `+`; automation `+` |
| Jade | CW XRD `++`; synchrotron XRD `+`; neutron `~` | texture `~`; microstructure `+`; PDF `-`; magnetic `-` | sequential `+`; joint `~`; batch/API `+`; automation `+` |
| Match! | CW XRD `++`; synchrotron XRD `+`; neutron/TOF/magnetic via FullProf | texture `~`; microstructure `~`; PDF `-` | sequential `~`; joint `~`; batch/API `+`; automation `+` |

## 2.5 Architecture and UX Lessons

- GSAS-II proves the value of broad scientific scope and Python scripting.
- FullProf proves the importance of magnetic and neutron maturity.
- TOPAS proves the value of a powerful model language and derivative/dependency management.
- MAUD proves that texture and microstructure need native combined-analysis support.
- Mantid proves that facility data reduction should be integrated rather than duplicated.
- Profex, HighScore, Jade, and Match! prove that guided UX and reporting matter for adoption.
- Spotlight proves that robust high-throughput refinement requires global search and HPC orchestration.
- Rongzai proves that LLM agents can help when they are tool-grounded and auditable.
