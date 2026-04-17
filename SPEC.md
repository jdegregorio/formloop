## Repo spec: Formloop

### Purpose

Formloop is the main application repo. Its role is to turn user intent into managed design work by orchestrating agents, maintaining state, invoking `cad-cli`, presenting results, and running developer evals. It is the system that feels like the product.

### What Formloop owns

Formloop owns:

* the manager agent
* specialist agents
* the constrained execution runtime
* the chat and design-review UI
* current design state
* run and revision state
* the internal design-loop review process
* the high-level `formloop` CLI
* dataset management
* developer eval orchestration
* run history and artifact plumbing

That means Formloop owns almost all workflow and product behavior, while `cad-cli` owns the deterministic CAD mechanics.

### What Formloop does not own

Formloop should not directly own:

* low-level CAD execution primitives
* renderer implementation details
* comparison math implementation
* artifact rendering internals
* reusable CLI-level packaging logic

Formloop should call into `cad-cli` for those capabilities.

### Agent and review responsibilities

Formloop should use the manager-plus-specialists structure already agreed:

* **Manager**
* **CAD Designer**
* **Design Researcher**
* **Render Specialist**
* **Review Specialist**
* **Eval Specialist**

Formloop shall use the OpenAI Agents SDK as its primary agent orchestration framework. OpenAI-backed runs should use the Responses path by default, while Anthropic-backed runs should be supported through the SDK's LiteLLM provider path.

The harness configuration surface should stay intentionally small and profile-based. At minimum it should provide checked-in `normal`, `dev_test`, and `eval` profiles with a shared thinking abstraction rather than exposing a broad matrix of provider-specific model controls.

The primary execution lifecycle is `run > revision`. A run is the single persistent design thread for one part, project, or eval case, and a revision is one persisted candidate iteration inside that run.

Before implementation begins, Formloop should check in versioned JSON Schemas for its primary state, API, and report contracts. Typed models may derive from those schemas later, but the checked-in schemas are the canonical v1 contract source. This first pass should fully define only the core run, revision, artifact-manifest, review-summary, and run-snapshot contracts, while keeping the remaining schemas intentionally simple.

The key conceptual split inside Formloop is between two different review modes.

**Internal design-loop review** is for normal user runs with no ground-truth geometry. It should evaluate the latest candidate against the normalized spec, rendered views, deterministic inspections, and at most one optional user-provided reference image. It can be iterative and tool-using.

The rendered PNG views are passed to the review or judge LLMs as multimodal image inputs, and the core visual comparison is between those rendered images and (a) the normalized spec and (b) any user-provided reference image. The rendered images are managed as durable per-run, per-revision artifacts so the review loop, evals, and UI all consume the same underlying files.

**Developer eval review** is for benchmarking runs where ground-truth geometry exists. It should combine deterministic calculators with agent judges, and may allow tool-using judges when needed for structured assessments like dimensional compliance.

That distinction belongs in Formloop, not in `cad-cli`, because it is fundamentally orchestration and evaluation policy rather than deterministic geometry tooling.

The manager should attempt a first CAD iteration by default. It should only ask clarifying questions before first-pass generation when critical gaps make a credible initial model impossible, such as missing core function, blocking interfaces, or must-hit dimensions or tolerances. When proceeding under ambiguity, the manager should record explicit assumptions.

In interactive mode, clarification answers resume the blocked run in place. In non-interactive mode, critical-gap detection should move the run into `blocked_on_clarification` with a structured clarification event rather than quietly producing a weak first pass.

A revision exists only after a candidate artifact bundle has been generated and persisted. Clarification, research, or spec cleanup alone do not create a revision. Revision ordinals remain monotonic within a run and do not reset after clarification or reopen.

Runs are intentionally reopenable over time. A run may move from `blocked_on_clarification` or `completed` back to `active`, while preserving prior outcomes in status history for inspection.

The CAD Designer should operate like a mechanical design engineer: standards-aware, manufacturable, and grounded in the current spec. It should proactively invoke the Design Researcher whenever named parts, mechanisms, standards, or conventions imply factual external knowledge that should guide the design.

### UI responsibilities

The UI is a mostly independent build that integrates with the harness through its HTTP programmatic interface. Detailed UI requirements live in `REQUIREMENTS_UI.md`; harness-side requirements live in `REQUIREMENTS_HARNESS.md`.

Formloop should present a design-review workspace with these primary surfaces:

* chat
* current spec
* an interactive GLB viewer for the latest candidate geometry (browser-native, Three.js via `GLTFLoader` as the recommended default, or `<model-viewer>` as an acceptable lighter option)
* the harness-produced multi-view render sheet as a secondary reference alongside the interactive viewer
* latest review summary
* artifact downloads

The interactive GLB viewer is the primary human-facing surface for geometry. The multi-view render sheet remains a first-class artifact because it is still the strongest visual signal for the agent-driven closed-loop review and is useful for human cross-reference. CAD-accurate measurement and feature interrogation belong on the harness side against STEP; the browser viewer is for mesh-level presentation only.

Detailed logs, tool calls, subagent history, and raw traces should exist, but remain collapsed by default. This keeps the UI intuitive while still making the system inspectable.

The programmatic interface is HTTP-only in v1 and uses asynchronous job semantics with polling. Clients poll for a current run snapshot plus append-only structured events rather than relying on streaming transports.

### CLI responsibilities

Formloop should expose the application/operator CLI:

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

This CLI is for:

* app lifecycle
* running a query outside the UI
* batch eval execution
* health checks
* updating the app

This is distinct from the `cad` command surface exposed by `cad-cli`.

The CLI should be profile-aware and should support `--interactive` and `--no-interactive` on `formloop run`, with the CLI defaulting to non-interactive behavior.

### Eval responsibilities

Formloop owns the dataset and benchmark layer.

Each eval case should manage:

* prompt
* normalized spec
* ground-truth STEP
* optional reference image
* tolerances
* tags

Each eval run should combine:

* deterministic metrics from geometry and artifacts
* structured agent-judge outputs

The qualitative eval contract should score `requirement_adherence` and `feature_coverage` independently on a `0..4` scale, report an equal-weight average aggregate, and include confidence on a `0.0..1.0` scale.

The deterministic geometry comparison contract should report shared volume, only-in-candidate volume, only-in-ground-truth volume, and composite IoU ratio.

That means Formloop owns the policy and orchestration for eval scoring, aggregation, CI reporting, and failure surfacing, even though it relies on `cad-cli` for deterministic geometry operations.

### Skills

Formloop's skill system shall comply with the open Agent Skills standard ([agentskills.io](https://agentskills.io/home); see also OpenAI's tools/skills guide at [developers.openai.com](https://developers.openai.com/api/docs/guides/tools-skills)). Aligning with an open standard preserves interoperability across agent platforms and reduces lock-in to any single vendor's skill format.

Versioned skills that invoke `cad-cli` should declare the stdout JSON fields they depend on, and the repository should declare one supported `cad-cli` release for preflight compatibility checks.

### Quality expectations

Formloop should prioritize:

* safe, reliable execution
* clean context boundaries
* explicit current state
* traceable artifacts
* low-noise user experience
* repeatable eval orchestration
* strong separation between product workflow and deterministic tooling

### Relationship with `cad-cli`

#### Basic Summary
The cleanest mental model is:

**Formloop asks questions and manages decisions.**
**`cad-cli` performs deterministic CAD work and returns artifacts plus structured JSON results.**

##### `cad-cli`

A reusable, deterministic CAD tool product that owns build, render, inspect, compare, and package operations, standardized around build123d, Blender, STEP, and GLB. It is headless, scriptable, CI-friendly, and usable outside Formloop.

##### Formloop

An agentic application that owns the manager and specialist harness, current design state, internal closed-loop review, developer eval orchestration, the UI, and the `formloop` application CLI. It uses `cad-cli` as its deterministic execution substrate.

#### Normal Flow/Handoffs
A normal flow should look like this:

1. Formloop receives a request for a run.
2. Formloop creates or resumes that run.
3. Formloop updates the current spec.
4. Formloop invokes `cad build`.
5. Formloop invokes `cad render`.
6. Formloop invokes `cad inspect` as needed for review.
7. Formloop may invoke `cad compare` in developer evals or revision comparison flows.
8. Formloop persists the current revision bundle.
9. Formloop presents outputs, decides whether to revise, may later reopen the run if needed, and records state.
