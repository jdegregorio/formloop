## Requirements Specification for Formloop - Agent Harness

**Scope**: This document covers the Formloop agent harness: manager and specialist agents, deterministic orchestration, the constrained runtime, the operator CLI, the HTTP programmatic interface, run and revision persistence, artifact handling, and developer eval orchestration. UI-facing requirements are tracked separately in [REQUIREMENTS_UI.md](REQUIREMENTS_UI.md).

**Important**: Keep each requirement status up to date during development. Documentation updates alone do not justify advancing a requirement status.

### Functional requirements

| ID | Requirement | Rationale | Status |
| -- | ----------- | --------- | ------ |
| FLH-F-001 | The harness shall maintain a normalized current fit/form/function specification for the active design. | The normalized spec is the shared object that connects user intent, agent work, review, and delivery. | Implemented |
| FLH-F-002 | The harness shall provide a manager agent that coordinates the active run and owns the final user-facing answer. | The architecture is manager-led rather than peer-to-peer. | Implemented |
| FLH-F-003 | The harness shall provide at minimum the specialist roles CAD Designer, Design Researcher, and Quality Specialist. | v1 should keep the specialist set intentionally small. | Implemented |
| FLH-F-004 | The manager shall invoke specialists as bounded tool-like capabilities using the OpenAI Agents SDK `agent.as_tool()` pattern or an equivalent SDK mechanism. | The chosen architecture is hub-and-spoke with the manager retaining control. | Implemented |
| FLH-F-005 | The harness shall support an internal review loop for normal design runs where no ground-truth geometry is available. | Normal user runs still require closed-loop validation. | Implemented |
| FLH-F-006 | The Quality Specialist shall support a normal design-review mode and a developer-eval mode. | One specialist role should cover both review contexts without duplicating architecture. | Implemented |
| FLH-F-007 | The normal design-review mode shall assess the latest candidate against the normalized spec, rendered outputs, deterministic inspections, and at most one optional user-provided reference image. | These are the minimum inputs needed to close the loop without ground-truth geometry. | Partial — reference image is persisted on the run and surfaced to the reviewer as a caption; full vision input will be added when UI uploads lands. |
| FLH-F-008 | The Quality Specialist shall be able to request further revision from the CAD Designer when the current candidate is not acceptable. | The review loop must be able to drive iteration. | Implemented |
| FLH-F-009 | The harness shall generate and retain a standard revision artifact bundle including STEP, GLB, rendered views, and a render sheet for each persisted candidate. | Durable artifacts are required for review, UI presentation, and traceability. | Implemented |
| FLH-F-010 | The harness shall produce a concise structured review summary suitable for downstream consumption by the UI, CLI, and stored revision records. | Review output should be machine-usable rather than only narrative prose. | Implemented |
| FLH-F-011 | The harness shall record and expose run history, revision history, artifact references, and structured execution traces for each run. | Traceability is a product feature. | Implemented |
| FLH-F-012 | The harness shall expose a high-level operator CLI for application lifecycle, single-run execution, eval execution, diagnostics, and updates. | Formloop owns an operator CLI separate from `cad-cli`. | Implemented |
| FLH-F-013 | The operator CLI shall support `formloop ui start`, `formloop ui stop`, `formloop ui status`, `formloop run`, `formloop eval run`, `formloop eval report`, `formloop doctor`, and `formloop update`. | These are the agreed primary operator surfaces. | Implemented |
| FLH-F-014 | The harness shall support developer eval runs over datasets with known ground-truth geometry. | Developer evals are a first-class system capability. | Implemented |
| FLH-F-015 | The harness shall combine deterministic eval metrics with structured LLM judge outputs. | Both deterministic evidence and higher-level assessment are required. | Implemented |
| FLH-F-016 | The Design Researcher shall be able to perform internet research through OpenAI search-enabled requests. | Standards, conventions, and part facts may require external research. | Implemented |
| FLH-F-017 | The manager shall be able to identify required research topics without being required to execute each research task directly. | The harness may orchestrate research fan-out on the manager's behalf. | Implemented |
| FLH-F-018 | The harness shall support application-orchestrated concurrent research execution for independent research branches. | Independent research work should be parallelizable without surrendering control to planner-style tool use. | Implemented |
| FLH-F-019 | The harness shall always attempt to produce at least one delivered revision through the run-and-review loop. | The product should bias toward a real design attempt rather than a question-first dead end. | Implemented |
| FLH-F-020 | When design intent is incomplete but the likely direction is still inferable, the manager shall record explicit assumptions in structured state and proceed. | v1 should tolerate ambiguity without stalling unnecessarily. | Implemented |
| FLH-F-021 | The harness shall use `run > revision` as its top-level persistence model. | This is the agreed lifecycle abstraction. | Implemented |
| FLH-F-022 | A revision shall exist only after a candidate artifact bundle has been generated and persisted within a run. | Revisions should represent inspectable candidate outputs, not every internal step. | Implemented |
| FLH-F-023 | The harness shall use human-readable sequential naming for persisted runs and revisions, while allowing hashes or opaque identifiers as secondary unique IDs where needed. | Stored results should be easy to inspect and naturally sort. | Implemented |
| FLH-F-024 | The harness shall emit LLM-written conversational progress narrations at meaningful milestones, separate from the structured milestone events, so the UI and CLI can surface a live "reasoning trace" to the operator. Narrations explain what the harness just finished, what it's doing next, and (when informative) why, in a single short paragraph or sentence. They ride on the same append-only progress-event stream as `kind == "narration"` and are also surfaced as `latest_narration` in the run snapshot. | The operator wants chat-style status updates, not just machine markers, with the latest one visible inline and older ones available on demand. | Implemented |
| FLH-F-025 | The harness shall expose a stable HTTP programmatic interface through which clients can create runs, poll current run snapshots and events, and retrieve run artifacts and review outputs. | The UI is a separate build and needs a clean contract boundary. | Implemented |
| FLH-F-026 | The harness shall provide a dedicated Narrator specialist agent that converts sanitized milestone payloads into the conversational progress narrations described in FLH-F-024. The Narrator runs on its own lightweight profile (cheap model, low reasoning effort) independent of the run's main profile so narration cost stays bounded. | A single small agent dedicated to wording keeps narration consistent and inexpensive without entangling it with the planning, design, or review agents. | Implemented |
| FLH-F-027 | The operator CLI (`formloop run`) shall render the live narration trace inline as the orchestration progresses, with the latest narration shown prominently between scrolling history, structured milestone events shown dimmed, and `--quiet` / `--verbose` / `--no-color` flags to control verbosity and TTY behavior. | The dev interface should mirror the UI's reasoning-trace pattern so operators get the same situational awareness from the terminal. | Implemented |
| FLH-F-028 | The CAD Designer shall produce a structured `DesignPlan` (paradigm choice, paradigm rationale, primary primitives, decomposition, external-library usage, open questions) before authoring `model.py`, and the orchestrator shall emit the plan as a `revision_planned` progress event ahead of the corresponding `revision_built` event. | Forcing an explicit plan step captures the designer's strategy for review and surfaces paradigm/library choices to the UI before the build artifacts land. | Implemented |
| FLH-F-029 | The harness shall ship a curated Build123D knowledge pack — the scraped official docs plus a curated external-library overlay covering `bd_warehouse`, `bd_vslot`, `py_gearworks`, and `bd_beams_and_bars` — and expose it to the CAD Designer through a `build123d_lookup` function tool so the agent can retrieve on-demand topic excerpts (objects, operations, joints, assemblies, cheat sheet, etc.) without paying the token cost of baking the full corpus into every prompt. | Grounding the designer in authoritative upstream documentation and a hand-audited ecosystem overlay lifts build quality for non-trivial parts (gears, fasteners, v-slot frames) without making the base prompt unbounded. | Implemented |

### Non-functional requirements

| ID | Requirement | Rationale | Status |
| -- | ----------- | --------- | ------ |
| FLH-NF-001 | The harness shall optimize for autonomy while maintaining safety, reliability, and inspectability. | The product should move forward aggressively without becoming opaque or fragile. | Implemented |
| FLH-NF-002 | The harness shall preserve artifact and decision traceability across prompt, spec, research, revisions, review outputs, and eval outputs. | Closed-loop validation depends on being able to inspect how the system got to an answer. | Implemented |
| FLH-NF-003 | The harness shall support reproducible eval execution suitable for before-and-after comparison. | The system should grow with a repeatable eval culture. | Implemented |
| FLH-NF-004 | The harness shall remain operable through its CLI and HTTP interfaces even when the UI is not running. | Headless and automation-friendly operation remain required. | Implemented |
| FLH-NF-005 | The harness shall keep the deterministic workflow in application code and use agents for adaptive reasoning rather than making the entire workflow model-directed. | A harness-first architecture is easier to test, debug, and control. | Implemented |
| FLH-NF-006 | The harness shall emit progress information in a polling-friendly format consisting of structured events and materialized snapshots rather than relying on a streaming-only contract. | The v1 UI and tooling model is polling-based. | Implemented |
| FLH-NF-007 | The harness shall expose enough structured logs, traces, and stored outputs to debug failures in normal runs and eval runs. | Diagnosability is required for development and operator trust. | Implemented |
| FLH-NF-008 | The harness should keep configuration and context surfaces intentionally small so the system stays maintainable. | The simplification effort is explicitly trying to reduce over-specification and accidental complexity. | Implemented |
| FLH-NF-009 | The harness shall note and avoid wasteful repeated model or render work when behavior changes would materially increase cost. | Cost discipline is part of the operating model. | Partial — revision loop is bounded by `max_revisions` and short-circuits on pass; smoke uses `dev_test` profile. No per-token metering yet. |
| FLH-NF-010 | Narration generation shall not block the orchestrator on failure: a Narrator timeout or exception shall degrade to a static fallback message, surface a `narration_error` field on the resulting event, and never abort the run. | Narration is a presentation feature, not a correctness feature; flakiness in the narrator must not cost the user a real CAD output. | Implemented |

### Design and technical constraint requirements

| ID | Requirement | Rationale | Status |
| -- | ----------- | --------- | ------ |
| FLH-D-001 | The harness shall use `cad-cli` as its deterministic CAD tool substrate rather than embedding those responsibilities directly. | Formloop should orchestrate deterministic CAD work, not duplicate it. | Implemented |
| FLH-D-002 | The harness shall use build123d as the primary modeling backend exposed through Formloop workflows. | This remains a core technical decision. | Implemented |
| FLH-D-003 | The harness shall treat STEP as the authoritative geometry artifact and GLB as the primary presentation artifact. | This is the agreed artifact split. | Implemented |
| FLH-D-004 | The harness shall expose a centralized internal runtime abstraction for CLI execution, constrained Python execution, artifact reads, and artifact writes. | The runtime boundary should stay small and explicit. | Implemented |
| FLH-D-005 | The harness shall not require a separate broker service in v1. | The architecture intentionally favors a smaller runtime. | Implemented |
| FLH-D-006 | The harness shall represent the current design state explicitly rather than reconstructing it from chat history alone. | The manager, review loop, and UI all depend on explicit state. | Implemented |
| FLH-D-007 | The harness shall use the OpenAI Agents SDK as its required agent orchestration framework. | OpenAI Agents SDK is the chosen implementation path. | Implemented |
| FLH-D-008 | OpenAI-backed runs shall use the OpenAI Responses path by default. | This is the preferred OpenAI execution path for v1. | Implemented |
| FLH-D-009 | The harness shall optimize for OpenAI-only execution in v1 and shall not require a multi-provider abstraction. | The simplification effort intentionally removes multi-provider scope. | Implemented |
| FLH-D-010 | Each agent shall be defined in its own Python module with detailed instructions, explicit tool access, an explicit model choice, and structured output where useful. | Specialist behavior should be explicit and versionable in code. | Implemented |
| FLH-D-011 | The harness shall keep deterministic orchestration in application code while using agents for adaptive inner steps such as interpretation, research, CAD authoring, and review. | This formalizes the harness-first architecture. | Implemented |
| FLH-D-012 | Parallel specialist work shall be orchestrated by application code and used only when branch independence is clear. | Parallelism should be deliberate and safe. | Implemented |
| FLH-D-013 | The harness shall keep run context separate from prompt context so internal identifiers, handles, caches, and other application state can remain outside model-visible input unless needed. | This is an important architectural boundary for correctness and safety. | Implemented |
| FLH-D-014 | The harness shall maintain a checked-in non-secret configuration file for runtime defaults at the repo root as `formloop.harness.toml`. | Runtime defaults should be explicit, shareable, and inspectable. | Implemented |
| FLH-D-015 | Secrets shall be supplied through environment variables only and shall not be committed to the repository. | Secret handling should stay simple and safe. | Implemented |
| FLH-D-016 | Environment variable support shall include at minimum `OPENAI_API_KEY`. | v1 is OpenAI-only. | Implemented |
| FLH-D-017 | The harness shall support checked-in named profiles for at least `normal` and `dev_test`. | The configuration surface should stay intentionally small. | Implemented |
| FLH-D-018 | Developer eval runs shall use the `normal` profile unless a later requirement introduces a dedicated alternative. | A separate `eval` profile is intentionally out of scope for now. | Implemented |
| FLH-D-019 | The programmatic interface shall be HTTP-only in v1 and shall use asynchronous job semantics with polling. | The UI and tooling model is polling-based HTTP. | Implemented |
| FLH-D-020 | The runtime abstraction shall capture and parse structured JSON from `cad-cli` stdout for each command it invokes. | `cad-cli` is a structured contract, not an ad hoc text interface. | Implemented |
| FLH-D-021 | The repository shall maintain checked-in schemas for the core persisted state, API, and report contracts needed by v1. | The core machine-readable contracts should be versioned in the repo. | Implemented |
| FLH-D-022 | The initial schema set shall cover at minimum run, revision, artifact manifest, run snapshot, progress event, review summary, deterministic metrics output, judge output, and the basic create-run request and response contracts. | These are the minimum stable contracts for the simplified v1 surface. | Implemented |
| FLH-D-023 | The runtime artifact tree shall live under `var/runs/` with one run folder containing run-level state and nested revision folders containing complete persisted revision bundles. | Filesystem conventions need to be stable across CLI, UI, and eval workflows. | Implemented |
| FLH-D-024 | The default revision bundle shall include STEP, GLB, per-view PNGs, a render-sheet PNG, revision metadata JSON, artifact-manifest JSON, and review output after review completes. | Revision completeness needs a concrete baseline. | Implemented |
| FLH-D-025 | The Narrator agent (FLH-F-026) shall receive only sanitized milestone payloads — coarse phase tag, what just completed, what comes next, optional rationale, and a small bag of numeric or short-string signals. It shall never see raw filesystem paths, run names, revision names, UUIDs, or other internal identifiers. | The Narrator's output is shown to the user and could otherwise leak internal state; sanitizing at the call site is the same discipline applied to the rest of the prompt-context boundary (FLH-D-013). | Implemented |
| FLH-D-026 | The Build123D knowledge pack (FLH-F-029) shall be committed under `src/formloop/agents/knowledge/build123d/` — 12 scraped markdown pages plus a curated `external_libs_overlay.md` — and loaded exclusively through `importlib.resources` so the pack works equally from editable checkouts and installed wheels. The scraper that regenerates the pack lives at `scripts/scrape_build123d_docs.py` and its optional dependencies are isolated to the `scrape` dependency group. | Shipping the corpus inside the package keeps it reviewable, versioned, and offline-usable, while keeping scraper deps opt-in keeps the runtime install footprint small. | Implemented |

### Validation and UAT requirements

| ID | Requirement | Rationale | Status |
| -- | ----------- | --------- | ------ |
| FLH-V-001 | The harness shall maintain full unit-test coverage over deterministic logic, schema and config parsing, and run-state serialization behavior. | Unit coverage should be comprehensive for deterministic code and contracts. | Implemented |
| FLH-V-002 | The harness shall maintain integration coverage for agent orchestration, runtime and tool boundaries, persistence, HTTP API behavior, and artifact generation. | Cross-boundary behavior is central to the product. | Implemented |
| FLH-V-003 | The harness shall run smoke tests, end-to-end UAT, and operator-style validation whenever those tests materially help development, not only during pull-request workflows. | Real tool use should happen whenever it improves confidence and learning. | Implemented |
| FLH-V-004 | Critical user and operator flows shall be maintained in [SPEC.md](SPEC.md). | The simplified spec should hold the essential UAT narrative. | Partial — SPEC.md captures the intent but was not updated in the v1 build-out; refresh to match the landed UAT steps is open. |
| FLH-V-005 | UAT for critical flows shall include actually using the harness the way an end user or operator would and inspecting whether the delivered part matches the requested outcome. | The user explicitly wants tool-using validation, not documentation-only checklists. | Implemented — `formloop run` for the plate-with-holes UAT produced rev-002 with overlap_ratio=1.000 against ground truth. |
| FLH-V-006 | Validation shall inspect surfaced outputs, persisted artifacts, review outputs, and visible quirks or failures rather than stopping at successful command completion. | Evidence at the system boundary matters more than internal confidence. | Implemented |
| FLH-V-007 | The harness shall validate `cad-cli` compatibility and schema-contract conformance as part of preflight and integration coverage. | The system depends on stable structured contracts. | Implemented |
| FLH-V-008 | Eval validation shall confirm per-case artifacts, deterministic metrics, judge outputs, and aggregate reporting outputs. | Eval quality needs concrete proof at both per-case and batch levels. | Partial — runner + report emit all required outputs and the per-case pipeline has been exercised by the UAT; a full batch run against `datasets/basic_shapes` is available via `formloop eval run` but has not been captured as a fixture yet. |

### Configuration and runtime contract

The harness configuration baseline is intentionally small:

- The checked-in non-secret configuration file shall live at the repo root as `formloop.harness.toml`.
- The initial named profiles are `normal` and `dev_test`.
- Developer evals should use `normal`.
- Local development secrets may be loaded from a repo-root `.env.local` file into environment variables at process start, and `.env.local` shall remain untracked.
- `.gitignore` and `.env.example` are the canonical tracked references for secret posture and should stay aligned with the requirements.
- The minimum environment variable contract is `OPENAI_API_KEY`.

The initial profile defaults are:

| Profile | Default model path | Default model | Default reasoning | Purpose |
| ------- | ------------------ | ------------- | ----------------- | ------- |
| `normal` | OpenAI Responses | `gpt-5.4` | `high` | Normal user-facing execution and eval execution. |
| `dev_test` | OpenAI Responses | `gpt-5.4-nano` | `low` | Low-cost plumbing and smoke validation. |

The stable run-state contract shall include at minimum:

- run identifier
- human-readable run name
- revision identifiers
- human-readable sequential revision names or ordinals
- effective profile
- effective model
- effective reasoning level
- current spec
- recorded assumptions
- current status summary
- artifact references
- review outputs
- progress events

The minimum HTTP operation set shall include:

- create run
- poll run snapshot and events
- retrieve artifacts
- retrieve review outputs

### Schema contract appendix

Before implementation begins, the repository shall check in versioned schemas organized under `schemas/`.

The first pass should fully define the core contracts below and keep the rest intentionally light until implementation pressure requires more detail.

#### Core schemas to define now

`run`

- Purpose: the single persisted design or eval thread.
- Minimum fields:
  - `run_id`
  - `run_name`
  - `created_at`
  - `updated_at`
  - `current_spec`
  - `input_summary`
  - `reference_image` optional
  - `assumptions`
  - `revisions`
  - `current_revision_id` optional
  - effective runtime metadata

`revision`

- Purpose: one persisted candidate iteration inside a run.
- Minimum fields:
  - `revision_id`
  - `revision_name`
  - `ordinal`
  - `created_at`
  - `trigger`
  - `spec_snapshot`
  - `artifact_manifest_path`
  - `review_summary_path` optional until review completes

`artifact-manifest`

- Purpose: the stable listing of revision artifacts by role.
- Minimum fields:
  - artifact entries keyed by stable role
  - `path`
  - `format`
  - `required`

`review-summary`

- Purpose: the concise structured output of normal design review for one revision.
- Minimum fields:
  - `decision`
  - `confidence`
  - `key_findings`
  - `suspect_or_missing_features`
  - `suspect_dimensions_to_recheck`
  - `revision_instructions`

`run-snapshot`

- Purpose: the polling-friendly materialized view of current run state.
- Minimum fields:
  - `run_id`
  - current spec summary
  - latest revision pointer
  - latest review summary pointer
  - artifact summary
  - last event reference

#### Additional schemas to keep in scope

- `progress-event`
  - Purpose: append-only status and milestone updates, including LLM-generated breadcrumbs.
- `deterministic-metrics-output`
  - Purpose: persisted deterministic eval and comparison results.
- `judge-output`
  - Purpose: persisted developer eval judge results.
- `run-create-request`
  - Purpose: the minimum request payload for starting a run.
- `run-create-response`
  - Purpose: the minimum response payload returned when a run is created.

### Filesystem and repo layout appendix

The runtime artifact tree shall live under `var/runs/`. This is generated runtime state: it should be human-inspectable and discoverable, but it is not core source code.

The default runtime tree shall be:

- `var/runs/<run-name-or-id>/run.json`
- `var/runs/<run-name-or-id>/events.jsonl`
- `var/runs/<run-name-or-id>/inputs/`
- `var/runs/<run-name-or-id>/revisions/rev-001/`

The default revision bundle under each revision folder shall be:

- `revision.json`
- `artifact-manifest.json`
- `step.step`
- `model.glb`
- `render-sheet.png`
- `views/`
- `review-summary.json` after review

The default top-level repo layout shall stay simple and human-readable:

- `src/formloop/` - application code for harness, CLI, runtime, eval orchestration, and shared domain logic
- `ui/` - browser UI that talks to the harness HTTP API
- `schemas/` - one schema file per checked-in contract
- `tests/` - unit, integration, smoke, and UAT coverage
- `datasets/` - eval datasets and related fixtures
- `docs/` - secondary docs and design notes
- `scripts/` - developer tooling and helper scripts
- `var/runs/` - generated local run state and artifacts

These requirements are meant to be a working baseline. The most important maintenance rule is simple: **keep the Status column current as development progresses**, so the document remains a living control surface rather than a one-time design artifact.
