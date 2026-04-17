# Formloop

Formloop is an agentic CAD application for turning natural language requirements into 3D geometry, iterating that geometry through closed-loop review, rendering consistent previews, and evaluating system quality with a repeatable developer eval harness.

It is the main application layer sitting above deterministic CAD tooling. Where `cad-cli` provides the portable geometry toolchain, Formloop owns orchestration, state, UX, and evaluation workflows.

## Purpose

Formloop should let a user:

- describe a part or revision in chat
- optionally provide one reference image per request
- receive intermediate progress updates through polling-backed run snapshots and events
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
- run and revision state
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
- user-facing progress reporting through async polling

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

It should use the OpenAI Agents SDK as the primary orchestration framework. OpenAI-backed runs should use the Responses path by default, and Anthropic-backed runs should be supported through the SDK's LiteLLM provider path.

Configuration should stay profile-based and intentionally narrow. The initial checked-in profiles should be `normal`, `dev_test`, and `eval`, with a shared thinking control such as `low`, `medium`, and `high`.

The core lifecycle is `run > revision`. A run is the single persistent design thread for one part, project, or eval case, and a revision is one persisted candidate iteration inside that run.

Before implementation begins, Formloop should check in versioned JSON Schemas for its primary state, API, and report contracts. Typed models may derive from those schemas later, but the checked-in schemas are the canonical v1 contract source. This first pass should fully define only the core run, revision, artifact-manifest, review-summary, and run-snapshot contracts, while keeping the remaining schemas intentionally simple.

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
The manager should attempt a first CAD iteration by default and only block for clarification when critical gaps make a credible first model impossible. When it proceeds under ambiguity, it should record explicit assumptions.
In interactive mode, clarification answers should resume the blocked run in place. In non-interactive mode, critical-gap detection should move the run into `blocked_on_clarification` with a structured clarification event.

A revision exists only after a candidate artifact bundle has been generated and persisted. Clarification, research, or spec cleanup alone do not create revisions. Revision ordinals remain monotonic within a run and do not reset after clarification or reopen.

Runs are intentionally reopenable over time. A run may move from `blocked_on_clarification` or `completed` back to `active`, while preserving prior outcomes in status history for inspection.

### Specialist agents

#### CAD Designer

Owns `build123d` modeling and model revisions. Produces authoritative geometry artifacts and responds to review feedback.
It should behave like a mechanical design engineer, prioritizing standards-aware, manufacturable, spec-grounded modeling, and should proactively involve the Design Researcher when external engineering facts would materially improve the design.

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

When the runtime invokes `cad-cli`, it should capture and parse structured JSON from stdout rather than relying on ad hoc text parsing.
The external programmatic interface should be HTTP-only in v1 and should use asynchronous job semantics with polling rather than transport streaming.

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

If a skill invokes `cad-cli`, it should also declare the target `cad-cli` release and the stdout JSON fields it depends on so `formloop doctor` can validate compatibility.

Suggested v1 skills:

- `build123d_modeling`
- `cad_artifact_conventions`
- `blender_rendering`
- `geometry_comparison`
- `design_research`
- `internal_design_review`
- `eval_execution`
- `reference_image_review`

## High-level application CLI specification

Formloop should expose a separate operator CLI.

```bash
formloop ui start
formloop ui stop
formloop ui status
formloop run "..."
formloop eval run datasets/basic_shapes
formloop eval report latest
formloop doctor
formloop update
```

`formloop run`, `formloop eval run`, and `formloop doctor` should all be profile-aware so the operator can switch between `normal`, `dev_test`, and alternate provider-backed configurations intentionally.
`formloop run` should support `--interactive` and `--no-interactive`, with the CLI defaulting to `--no-interactive`.

This CLI is for:

- application lifecycle
- running agent queries outside the UI
- batch eval execution
- health checks
- updating the application

The conceptual split remains:

- `cad-cli` provides the deterministic `cad` command surface
- Formloop provides orchestration and application lifecycle

## Artifact model

The system should standardize artifacts early.
The stable runtime filesystem shape should be `var/runs/<run-id>/revisions/`.

### Authoritative artifacts

- STEP
- source model
- metadata JSON

### Presentation artifacts

- GLB
- per-view PNGs
- render sheet PNG

### Internal review artifacts

- review summary JSON
- review notes
- measurement outputs
- optional reference-image comparison outputs

### Eval artifacts

- per-case outputs
- compare metrics
- judge outputs
- aggregated reports

Each persisted revision bundle should contain at minimum:

- STEP
- GLB
- per-view PNGs
- render sheet PNG
- revision metadata JSON
- artifact manifest JSON

After review completes, that same revision bundle should also contain:

- review summary JSON
- review notes or review output

The runtime artifact tree should stay human-inspectable and live under `var/runs/`, while core source code remains in clearly named top-level directories such as `src/formloop/`, `ui/`, `schemas/`, `tests/`, `datasets/`, `skills/`, `docs/`, and `scripts/`.

## Human interface specification

The UI should feel like a design review workspace, not a trace console.

### Primary surfaces

#### Chat

The main interaction surface.

#### Current spec

A distilled, canonical summary of the current fit, form, and function target. This is the target the system believes it is building, not a raw transcript.

#### Latest geometry

The primary preview surface. Show the latest interactive GLB viewer and make the latest render sheet plus individual views available as secondary references.

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
V1 should support one optional PNG or JPEG reference image per request.

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
Formloop should treat `cad-cli` as a structured JSON-stdout contract and pin a supported release in checked-in config.

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

## Developer eval specification

Developer evals are different from normal user runs because here there is ground-truth geometry and the goal is repeatable benchmarking.

These evals should be less agentic by default than the normal design loop, but they may still use an agent judge that performs multiple tool calls if that improves evaluation quality.

### Purpose of developer evals

Developer evals answer questions like:

- did the system generate the right geometry from the prompt
- how close is candidate geometry to ground truth
- did the system include all required features
- are key dimensions accurate
- are regressions appearing over time

### Dataset structure

Each case should contain:

- prompt
- normalized spec
- ground-truth STEP
- optional reference image
- optional tolerances
- tags

Suggested datasets:

- `basic_shapes`
- `feature_shapes`
- `reference_parts`

### Eval scoring model

Eval scoring should combine two classes of evaluators.

#### A. Deterministic calculators

These produce hard metrics from geometry and artifacts.

Required v1 metric outputs:

- shared volume
- only-in-ground-truth volume
- only-in-candidate volume
- composite IoU ratio
- artifact presence and completeness when relevant

These should be the foundation of objective regression tracking.

#### B. Agent eval judges

These produce higher-level quality assessments that are difficult to express as a single deterministic formula.

Required v1 qualitative dimensions:

- `requirement_adherence` on a `0..4` scale
- `feature_coverage` on a `0..4` scale
- equal-weight average aggregate
- confidence on a `0.0..1.0` scale

Judge prompts should explicitly instruct the judge to ignore background color, lighting, edge rendering style, and geometry color, and to evaluate shape, geometry, and requested features only.

These agent judges can be simple or tool-using.

### Tool-using eval judges

The eval routine is less agentic by default, but it is reasonable to allow an LLM judge to use tools to complete an evaluation goal.

For example, an eval judge for dimensional compliance might:

- inspect bounding box
- measure hole spacing
- measure thickness
- compare those values to spec tolerances
- return a structured dimensional compliance score

So the eval judge may be agentic in implementation, even though the overall eval framework is not an open-ended design loop.

### Eval outputs

Each eval case should produce:

- deterministic metrics JSON
- judge outputs JSON
- short markdown summary
- artifact bundle
- pass/fail or score status

Each batch eval should produce:

- aggregate metric summary
- per-dataset summary
- failure shortlist
- trend-ready outputs for CI

## Recommended eval dimensions

### Run success

- did the system complete
- were required artifacts produced

### Deterministic geometric accuracy

- shared volume
- only-in-ground-truth
- only-in-candidate
- composite IoU ratio

### Structured quality judgment

- requirement adherence score
- feature coverage score
- equal-weight aggregate score
- confidence

### Artifact completeness

- render success
- packaging completeness
- source and metadata presence

## CI integration

GitHub Actions on push to `main` should:

- run a batch eval suite
- publish aggregate results
- attach failed-case artifacts
- surface regressions clearly

A smaller smoke subset should run on PRs.

CI results should combine:

- deterministic calculator outputs
- agent judge outputs

That gives both objective numeric regressions and higher-level quality assessment.

## Run lifecycle

### Normal user run

A normal user run should look like this:

1. user provides a design request into a run, optionally with one reference image
2. Formloop creates or resumes that run
3. manager writes or updates current spec
4. manager invokes Design Researcher if needed
5. manager invokes CAD Designer to create or revise geometry
6. geometry is exported to STEP and GLB
7. Render Specialist produces preview outputs
8. the current revision bundle is persisted
9. Review Specialist evaluates the current candidate against the spec, inspection results, renders, and any reference image
10. if needed, Review Specialist sends revision feedback back to CAD Designer
11. loop continues until stop criteria are met or caps require a graceful landing
12. UI updates current spec, latest geometry, review summary, run history, and artifacts

### Developer eval run

A developer eval run should look like this:

1. load dataset case
2. run generation from prompt/spec
3. produce artifacts
4. run deterministic compare calculators against ground truth, including shared volume, only-in-ground-truth volume, only-in-candidate volume, and IoU
5. run structured agent judges for `requirement_adherence` and `feature_coverage`
6. compute equal-weight aggregate scoring and confidence
7. publish per-case and batch outputs

## Non-goals for the core version

The core version should not try to do all of these at once:

- manufacturing or slicing validation in the main loop
- distributed execution
- multiple modeling backends
- highly decomposed micro-repo tool architecture
- advanced publishing pipelines
- technical drawing workflows as the default user path

## Optional addendum: 3D printing validation

This remains intentionally outside the core design.

If added later, the right extension point is:

```bash
cad validate ...
```

This should be downstream from the core design loop and optional.

A future two-layer approach could include:

- a geometry-aware pre-analysis layer
- a slicer-backed validation layer, with PrusaSlicer as the portable default and Bambu Studio as an optional target-specific second pass

For a future MVP, the most useful validation signals would be:

- unsupported overhang area
- bridge risk
- mid-air islands
- support-contact pain proxy

If added later, this should appear in three places:

- `cad validate` in the CLI
- an optional Printability panel in the UI
- an optional manufacturability score bucket in evals

## Relationship to cad-cli

Formloop should call into `cad-cli` for deterministic CAD operations rather than reimplement them internally.

A useful boundary:

- if it is a portable geometry tool, it belongs in `cad-cli`
- if it is agent behavior, UX, state, or evaluation logic, it belongs in Formloop

## Initial development priorities

1. define core run, revision, and artifact schemas
2. establish app-to-`cad-cli` command contracts
3. implement the first end-to-end part generation loop
4. add revision and review loop support
5. stand up preview and artifact delivery surfaces
6. implement developer eval harness with known-truth datasets
7. instrument traceability, regression detection, and operator feedback

## Status

Early repo setup. The immediate goal is to lock in architecture, boundaries, and operating expectations before full scaffolding begins.
