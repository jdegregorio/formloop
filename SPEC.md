## Repo Spec: Formloop

<!-- REQ: FLH-V-004 — keep this spec aligned with the harness implementation. -->

### Purpose

Formloop is the main application for an agentic CAD system. It turns natural-language design intent into managed CAD work by orchestrating agents, maintaining explicit design state, invoking `cad-cli`, presenting artifacts, and running developer evals.

The product boundary is simple:

- Formloop owns orchestration, state, UX, run history, and eval policy.
- `cad-cli` owns deterministic CAD execution and artifact generation.

### What Formloop Owns

Formloop owns:

- the manager agent
- specialist agents
- the harness runtime and orchestration logic
- the chat and design-review UI
- normalized current design state
- run and revision persistence
- review and eval policy
- the `formloop` operator CLI
- dataset and eval orchestration
- artifact and traceability plumbing

Formloop should not duplicate deterministic geometry logic that belongs in `cad-cli`.

### Architecture

#### Hub-and-Spoke Manager

Formloop shall use the OpenAI Agents SDK as its orchestration framework.

The v1 harness architecture is manager plus a small set of specialists and
harness-managed direct model calls:

- **Manager**
- **CAD Designer**
- **Reviewer**
- **Judge**
- **Narrator**
- **Direct research call** (not an agent)

The manager owns the user-facing objective and the final answer. Specialists do not take over the run. They are exposed to the manager as callable capabilities through `agent.as_tool()` or the equivalent SDK pattern so the manager keeps control of orchestration and output.

Each agent should live in its own Python module with:

- a stable name
- detailed instructions
- an explicit tool surface
- an explicit model choice
- structured output when machine-readable results are useful

#### Deterministic Outer Workflow

Formloop should follow a harness-first architecture.

The application code owns deterministic workflow decisions such as:

- creating or resuming a run
- maintaining the normalized current spec
- deciding when to invoke specialists
- deciding when to fan out independent research work
- persisting artifacts and revision records
- deciding whether to loop for another revision
- deciding what to surface to the UI and CLI

Agents handle the adaptive parts inside that workflow:

- interpreting design intent
- authoring CAD source
- reviewing candidate outputs
- synthesizing findings into user-facing updates

Harness-managed direct OpenAI Responses calls handle focused research topics
with built-in `web_search`. They are not agent run loops.

This keeps the core run and revision loop controlled by the harness while still using agents for the fuzzy reasoning steps.

#### Specialist Contracts

The specialist roles are intentionally small:

- **CAD Designer** owns CAD source authoring. The harness owns artifact-oriented
  final `cad-cli` build, inspect, render, and revision execution.
- **Reviewer** owns normal design-loop review against the current spec, artifacts, and optional reference image.
- **Judge** owns developer-eval judgment against ground-truth data plus deterministic metrics.
- **Narrator** owns low-cost progress narration from sanitized milestone payloads.

Design research is deliberately not a specialist agent in the current harness.
The manager may identify research topics, then the harness fans those topics out
as one direct search-enabled Responses request per topic.

#### Parallel Research

Independent research topics may be executed concurrently when the harness can prove the branches are independent. This concurrency should be orchestrated by the application, such as with `asyncio.gather`, rather than delegated to planner-style model behavior.

The manager may identify required research topics without personally performing every delegation step. The harness may translate those identified topics into concurrent direct research calls and return the results to the manager for synthesis. Each topic is bounded to one built-in web-search tool call so research remains predictable and inspectable.

#### Run Context vs Prompt Context

Formloop should keep internal state separate from model-visible prompt context.

- Prompt context is what the model needs to reason about the current turn.
- Run context is what the application needs to track execution, state, identifiers, caches, and other internal handles.

Sensitive or low-signal internal state should stay in run context unless the model genuinely needs it.

### Run and Revision Model

The top-level lifecycle is `run > revision`.

- A run is the persistent design or eval thread.
- A revision is one persisted candidate iteration inside that run.

The harness should attempt a real first design pass rather than centering the product around upfront questions. When requirements are incomplete but the likely direction is still inferable, the manager may make reasonable assumptions, record them in structured state, and proceed.

The normal loop is:

1. normalize the request into the active spec
2. identify any research needed
3. generate a candidate revision
4. persist the revision bundle
5. review the candidate
6. revise again if the review indicates more work is needed
7. deliver the latest revision and review outcome

A revision exists only after a candidate artifact bundle has been generated and persisted.

Runs and revisions should use human-readable sequential naming so stored results are easy to inspect and naturally sort in filesystem and UI views. Hashes may still exist as secondary unique identifiers when needed.

### Artifacts

Formloop should standardize artifacts early.

- STEP is the authoritative geometry artifact.
- GLB is the primary presentation artifact.
- rendered PNG views and a render sheet are shared review artifacts and optional UI/operator artifacts.
- review outputs and eval outputs are persisted alongside revision data.

Artifact bundles should remain easy to inspect after the fact so a run can be audited from prompt through delivered revision.

### UI Responsibilities

Detailed UI requirements live in [REQUIREMENTS_UI.md](REQUIREMENTS_UI.md).

At a high level, the UI should present a design-review workspace built around:

- chat
- a concise normalized-spec plus latest-review summary
- an interactive GLB viewer
- artifact downloads
- collapsed-by-default traceability surfaces

The default UI layout is a three-pane workspace:

- left half: chat thread and composer
- top-right: concise normalized-spec plus latest-review summary
- bottom-right: interactive GLB viewer

Render sheet and per-view images are optional non-primary surfaces (for example downloadable artifacts or debug/operator affordances), not required default panes.

The UI should consume a polling-friendly HTTP interface from the harness. Progress is surfaced through two complementary channels on the same append-only event stream:

- **Structured milestone events** — machine-readable markers (`spec_normalized`, `revision_built`, `review_completed`, `delivered`, …) used for state transitions and analytics.
- **Narration events** (`kind == "narration"`) — short conversational status updates written by a dedicated lightweight Narrator agent (FLH-F-026). Each narration carries a coarse `phase` tag (`plan` / `research` / `revision` / `review` / `final` / `failure`) and answers what just finished, what's starting next, and why when it's informative. The latest narration is also surfaced as `latest_narration` on the run snapshot so polling clients don't need to scan the event tail.

The UI renders the latest narration as a de-emphasized line between the operator's last message and the agent's eventual final answer — like a reasoning-trace component. As new narrations arrive, the previous one collapses into history; the operator can expand a "show trace" affordance to see the full sequence. The `formloop run` CLI mirrors this behavior in the terminal: latest narration in place above the next final block, structured milestones dimmed, with `--quiet` and `--verbose` flags to control verbosity (FLH-F-027).

UI trace labels should prefer stable event semantics (phase + milestone + narration) over internal role naming so UX remains consistent when harness internals evolve.

### CLI Responsibilities

Formloop should expose a high-level operator CLI separate from the `cad` surface:

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

This CLI owns:

- app lifecycle
- single-run execution outside the UI
- eval execution
- health checks
- updating the app

The CLI should be profile-aware, but v1 should keep profiles small:

- `normal`
- `dev_test`

Developer evals should use the `normal` profile unless a later requirement introduces a dedicated alternative.

### Eval Responsibilities

Formloop owns the dataset and benchmark layer.

Each eval case should carry the minimum information needed for repeatable benchmarking:

- prompt
- normalized spec
- ground-truth STEP
- optional reference image
- tags

Each eval run should produce:

- deterministic metrics JSON
- judge outputs JSON
- a short summary
- per-case artifacts
- aggregate reporting outputs

Formloop owns eval orchestration, scoring policy, aggregation, and failure surfacing even when deterministic geometry operations come from `cad-cli`.

### Critical User and Operator Stories

These stories define the essential v1 behavior:

1. A user creates a new part from a prompt and receives a delivered revision with inspectable artifacts and review feedback.
2. A user gives an ambiguous prompt, the manager makes reasonable assumptions, records them, and still produces a first revision.
3. A request implies external standards or conventions, research is performed, and the findings inform the design before or during revision generation.
4. Review feedback identifies issues, the loop produces another revision, and the updated revision is persisted and surfaced clearly.
5. An operator runs an eval case against known truth and receives deterministic metrics, judge outputs, and aggregate reporting.
6. An AI coding agent or operator performs end-to-end UAT by actually using the harness and inspecting whether the delivered part matches the requested outcome, including visible quirks or failures.

### Relationship with `cad-cli`

The clean mental model is:

- Formloop manages the design loop, eval loop, and product behavior.
- `cad-cli` performs deterministic CAD work and returns artifacts plus structured JSON.

Formloop should reach `cad-cli` through harness tools and runtime functions rather than quietly re-implementing those operations inside agent prompts or app logic.
