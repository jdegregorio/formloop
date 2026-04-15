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

The key conceptual split inside Formloop is between two different review modes.

**Internal design-loop review** is for normal user runs with no ground-truth geometry. It should evaluate the latest candidate against the normalized spec, rendered views, deterministic inspections, and optional user-provided reference images. It can be iterative and tool-using.

The rendered PNG views are passed to the review/judge LLMs as **multimodal image inputs**, and the core visual comparison is between those rendered images and (a) the normalized spec and (b) any user-provided reference image. The rendered images are managed as durable per-run, per-revision artifacts so the review loop, evals, and UI all consume the same underlying files. 

**Developer eval review** is for benchmarking runs where ground-truth geometry exists. It should combine deterministic calculators with agent judges, and may allow tool-using judges when needed for structured assessments like dimensional compliance. 

That distinction belongs in Formloop, not in `cad-cli`, because it is fundamentally orchestration and evaluation policy rather than deterministic geometry tooling.

### UI responsibilities

The UI is a mostly independent build that integrates with the harness through its programmatic interface. Detailed UI requirements live in `REQUIREMENTS_UI.md`; harness-side requirements live in `REQUIREMENTS_HARNESS.md`.

Formloop should present a design-review workspace with these primary surfaces:

* chat
* current spec
* an interactive GLB viewer for the latest candidate geometry (browser-native, Three.js via `GLTFLoader` as the recommended default, or `<model-viewer>` for a lighter option)
* the harness-produced multi-view render sheet as a secondary reference alongside the interactive viewer
* latest review summary
* artifact downloads

The interactive GLB viewer is the primary human-facing surface for geometry. The multi-view render sheet remains a first-class artifact because it is still the strongest visual signal for the agent-driven closed-loop review and is useful for human cross-reference. CAD-accurate measurement and feature interrogation belong on the harness side against STEP; the browser viewer is for mesh-level presentation only.

Detailed logs, tool calls, subagent history, and raw traces should exist, but remain collapsed by default. This keeps the UI intuitive while still making the system inspectable. 

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

That means Formloop owns the policy and orchestration for eval scoring, aggregation, CI reporting, and failure surfacing, even though it relies on `cad-cli` for deterministic geometry operations. 

### Skills

Formloop's skill system shall comply with the open Agent Skills standard ([agentskills.io](https://agentskills.io/home); see also OpenAI's tools/skills guide at [developers.openai.com](https://developers.openai.com/api/docs/guides/tools-skills)). Aligning with an open standard preserves interoperability across agent platforms and reduces lock-in to any single vendor's skill format.

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
**`cad-cli` performs deterministic CAD work and returns artifacts plus structured results (as a skill)**


##### `cad-cli`

A reusable, deterministic CAD tool product that owns build, render, inspect, compare, and package operations, standardized around build123d, Blender, STEP, and GLB. It is headless, scriptable, CI-friendly, and usable outside Formloop.  

##### Formloop

An agentic application that owns the manager/specialist harness, current design state, internal closed-loop review, developer eval orchestration, the UI, and the `formloop` application CLI. It uses `cad-cli` as its deterministic execution substrate. 

#### Normal Flow/Handoffs
A normal flow should look like this:

1. Formloop receives a request.
2. Formloop updates the current spec.
3. Formloop invokes `cad build`.
4. Formloop invokes `cad render`.
5. Formloop invokes `cad inspect` as needed for review.
6. Formloop may invoke `cad compare` in developer evals or revision comparison flows.
7. Formloop presents outputs, decides whether to revise, and records state. 
