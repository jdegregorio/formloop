# Formloop

Formloop is an agentic CAD application for turning natural language requirements into 3D geometry, iterating that geometry through closed-loop review, rendering consistent previews, and evaluating system quality with a repeatable developer eval harness.

It is the main application layer sitting above deterministic CAD tooling. Where `cad-cli` provides the portable geometry toolchain, Formloop owns orchestration, state, UX, and evaluation workflows.

## Purpose

Formloop should let a user:

- describe a part or revision in chat
- optionally provide reference images
- receive intermediate progress updates
- inspect the current fit, form, and function spec
- view the latest rendered geometry
- review lightweight quality findings from the internal loop
- download final artifacts
- run developer evals over datasets with known truth

## System goals

The system is optimized for:

- safe and reliable execution
- low operational complexity
- deterministic core tools
- clean context management for agents
- strong artifact traceability
- a human interface that is intuitive without being overloaded

## Architectural decisions

### Modeling

Formloop uses `build123d` through the deterministic `cad-cli` tool layer as the primary modeling backend. This supports a long-lived Python-native CAD system with explicit geometry objects and maintainable software structure.

### Rendering

Blender is the sole standard renderer. Formloop should treat rendering as a downstream presentation step, with:

- STEP as the authoritative CAD artifact
- GLB as the presentation and rendering artifact

### Comparison

Geometry comparison is a core capability, not a side utility. The preferred path is:

1. align solids when needed
2. perform exact CAD-solid comparison where possible
3. compute overlap and delta metrics on aligned solids

### Packaging split

- `cad-cli` owns deterministic build/render/compare/inspect/package capabilities
- Formloop owns agent orchestration, UI, run state, evals, and artifact plumbing

## Repository scope

### In scope

- manager and specialist agent workflows
- constrained execution runtime
- user interface and chat surfaces
- high-level operator CLI
- skills, resources, and prompt context
- current design state and revision state
- eval orchestration and dataset management
- run history, artifacts, and traceability plumbing

### Out of scope

- becoming a second CAD kernel
- embedding geometry logic that belongs in `cad-cli`
- coupling UI logic directly to renderer internals
- hiding unvalidated agent output behind polished visuals

## Functional layers

### A. Agent harness

Responsible for:

- decomposition
- context management
- specialist routing
- internal review loops
- user-facing progress reporting

### B. Human interface

Responsible for:

- chat interaction
- current spec display
- preview surfaces
- review summaries
- artifact access

### C. Deterministic CAD tool layer

Responsible for build, render, compare, inspect, and packaging through the `cad` command surface provided by `cad-cli`.

### D. Evaluation layer

Responsible for developer eval datasets, scoring, regression tracking, and CI integration.

## Agent harness specification

The harness should be multi-agent, but intentionally small and controlled in v1.

### Manager agent

The manager is responsible for:

- understanding the user request
- maintaining the active fit, form, and function spec
- deciding whether external research is needed
- choosing which specialist to invoke
- deciding when another internal review pass is needed
- deciding when results are ready to present
- producing concise intermediate updates

The manager should not do heavy CAD authoring directly.

### Specialist agents

#### CAD Designer

Owns `build123d` modeling and model revisions. Produces authoritative geometry artifacts and responds to review feedback.

#### Design Researcher

Finds dimensions, standards, fastener sizes, and other external factual inputs needed to complete the design.

#### Render Specialist

Produces render outputs from GLB artifacts using Blender. Does not edit geometry.

#### Review Specialist

Owns the internal review loop for design runs without ground truth. Evaluates whether the latest candidate appears to satisfy the current spec, compares rendered outputs to any reference images, requests measurements or inspections as needed, and sends revision feedback back to the CAD Designer.

#### Eval Specialist

Owns developer-facing evaluation runs where truth data is known. Executes or coordinates deterministic scoring and agent-judge scoring over datasets.

This split matters:

- the **Review Specialist** is for the internal design loop
- the **Eval Specialist** is for developer benchmarking and CI

## Runtime interface

Formloop needs one centralized internal runtime abstraction. It does not need a broker service.

Conceptually, the runtime only needs to do four things:

- run CLI commands
- run Python in a constrained environment
- read artifacts
- write artifacts

That is enough for:

- safe terminal access to `cad`
- Python-side `build123d` logic
- render orchestration
- artifact management

## Skill system

Skills are reusable capability guides, not tiny macros.

Each skill should define:

- purpose and scope
- which agent uses it
- relevant tools and commands
- common workflows
- conventions
- common failures and recovery patterns
- expected artifacts

Suggested v1 skills:

- `build123d_modeling`
- `cad_artifact_conventions`
- `blender_rendering`
- `geometry_comparison`
- `design_research`
- `internal_design_review`
- `eval_execution`
- `reference_image_review`

## Human interface specification

The UI should feel like a design review workspace, not a trace console.

### Primary surfaces

#### Chat

The main interaction surface.

#### Current spec

A distilled, canonical summary of the current fit, form, and function target. This is the target the system believes it is building, not a raw transcript.

#### Latest geometry

The primary preview surface. Show the latest render sheet and allow access to individual views.

#### Latest review summary

A concise summary of what the internal review loop thinks about the current candidate. This may include:

- whether the design appears to satisfy the spec
- open concerns
- revision suggestions
- reference-image comparison notes if a reference image was provided

#### Artifacts

A download surface for:

- STEP
- GLB
- render sheet PNG
- model source
- compare outputs when present
- eval outputs when applicable

### Secondary surfaces

These should remain collapsed by default:

- tool call history
- subagent call history
- raw logs
- intermediate artifacts
- detailed review traces
- detailed eval traces

## Internal design loop

During a normal user design run, there is usually no ground-truth STEP file. The system therefore needs an internal review loop that judges the candidate against:

- the normalized current spec
- the produced geometry
- the rendered outputs
- optionally a reference image supplied by the user

### Goal of the internal review loop

The goal is not to match truth geometry.

The goal is: does the current candidate appear to satisfy the requested fit, form, and function well enough to stop, or should the agent revise again?

### Inputs to internal review

The Review Specialist may use:

- current spec summary
- latest model metadata
- render sheet and view images
- basic deterministic inspections from `cad inspect`
- optional `cad compare` against a user-provided reference image derivative or later a proxy geometry
- optional user-provided reference image directly

### Closed-loop review tools

The internal loop should support at least these review mechanisms:

#### Spec compliance review

Check whether requested features seem present and whether the design appears aligned with the normalized spec.

#### Dimensional spot-checks

Request deterministic measurements through `cad inspect` or geometry queries to validate key dimensions.

#### Feature presence checks

Confirm that holes, chamfers, rounds, pockets, bosses, tabs, or other expected features appear to exist.

#### Reference image review

If the user provides a reference image, compare the rendered outputs against that image as part of closed-loop review. This is not exact geometric truth, but it is still useful for catching gross shape mismatch, missing features, wrong proportions, wrong silhouette, and wrong orientation.

#### Render-based visual review

Use the latest front, right, top, and iso renders to assess whether the candidate looks coherent and complete.

### Internal review outputs

The Review Specialist should produce a structured review result such as:

- overall pass or revise
- confidence
- key findings
- missing or suspect features
- suspect dimensions to re-check
- reference-image mismatch notes
- revision instructions for the CAD Designer

### Important boundary

This internal review loop is still agentic.

It can use multiple tool calls and multiple passes when needed.

For example, the review agent might:

- inspect overall bounding box
- inspect hole diameters
- re-render an alternate camera view
- compare render silhouette to a reference image
- then decide whether to revise geometry

So the design loop can be iterative and tool-using, even though it does not have ground-truth geometry.

## Deterministic CLI specification for cad-cli

The external contract should be simple and unified.

```bash
cad build ...
cad render ...
cad compare ...
cad inspect ...
cad package ...
```

### `cad build`

Purpose: execute or parameterize a `build123d` model and emit standard artifacts.

Inputs may include:

- model source
- parameter file
- working directory
- output directory

Outputs should include:

- STEP
- GLB
- metadata
- optionally STL
- optionally normalized source snapshot

### `cad render`

Purpose: render a GLB model into deterministic preview assets using Blender.

Inputs may include:

- GLB path
- render spec
- output directory

Outputs should include:

- front view
- right view
- top view
- iso view
- composite contact sheet
- render metadata

### `cad compare`

Purpose: compare two geometries when two geometries are available.

Typical uses:

- candidate vs ground truth in evals
- candidate vs prior revision
- candidate vs imported reference geometry
- optional future derived geometry comparisons

Outputs should include:

- metrics JSON
- short summary
- overlap metrics
- optional diff solids or meshes
- optional visual review assets

### `cad inspect`

Purpose: provide lightweight deterministic inspection without requiring full comparison.

Typical uses:

- bounding box
- overall dimensions
- thickness checks
- hole diameters
- center distances

## Relationship to cad-cli

Formloop should call into `cad-cli` for deterministic CAD operations rather than reimplement them internally.

A useful boundary:

- if it is a portable geometry tool, it belongs in `cad-cli`
- if it is agent behavior, UX, state, or evaluation logic, it belongs in Formloop

## Initial development priorities

1. define core run-state and artifact model
2. establish app-to-`cad-cli` command contracts
3. implement the first end-to-end part generation loop
4. add revision and review loop support
5. stand up preview and artifact delivery surfaces
6. implement developer eval harness with known-truth datasets
7. instrument traceability, regression detection, and operator feedback

## Status

Early repo setup. The immediate goal is to lock in architecture, boundaries, and operating expectations before full scaffolding begins.
