## Requirements specification for Formloop - Agent Harness

**Scope**: This document covers requirements for the Formloop agent harness: the manager and specialist agents, the constrained execution runtime, the internal design-loop review, developer eval orchestration, the operator CLI, the HTTP programmatic interface, dataset management, run history, and artifact plumbing. UI-facing requirements are tracked separately in [REQUIREMENTS_UI.md](REQUIREMENTS_UI.md).

**Important**: Keep each requirement status up to date during development. Include comments that reference requirements in-code wherever possible.

### Functional requirements

| ID        | Requirement | Rationale | Status   |
| --------- | ----------- | --------- | -------- |
| FLH-F-001 | The harness shall maintain a normalized current fit/form/function specification for the active design. | The current spec is a core user-facing and agent-facing object in the agreed design. | Proposed |
| FLH-F-002 | The harness shall provide a manager agent that coordinates the active run and delegates to specialist agents. | The agreed architecture uses a manager-plus-specialists harness. | Proposed |
| FLH-F-003 | The harness shall provide at minimum the specialist roles CAD Designer, Design Researcher, Render Specialist, Review Specialist, and Eval Specialist. | These are the agreed initial specialist boundaries. | Proposed |
| FLH-F-004 | The harness shall support an internal review loop for normal design runs where no ground-truth geometry is available. | The project explicitly distinguishes internal design-loop review from developer evals. | Proposed |
| FLH-F-005 | The harness's internal review loop shall assess the latest candidate against the normalized spec, rendered outputs, deterministic inspections, and at most one optional user-provided reference image. | This is the agreed basis for closed-loop design review without ground truth. | Proposed |
| FLH-F-006 | The harness shall support deterministic measurement and inspection requests inside the internal review loop. | Internal review requires concrete checks, not only visual judgment. | Proposed |
| FLH-F-007 | The harness shall support reference-image review as a closed-loop review tool when the user provides a reference image. | Reference-image comparison is an explicitly requested review capability. | Proposed |
| FLH-F-008 | The harness shall allow the Review Specialist to request further revision from the CAD Designer when the current candidate is not acceptable. | The review loop must be able to drive iterative improvement. | Proposed |
| FLH-F-009 | The harness shall generate and retain the standard multi-view rendered images of the latest candidate geometry for use in the closed-loop review process. | Rendered images remain the primary visual signal for agent-driven review, even when human-facing UIs move to interactive GLB viewing. | Proposed |
| FLH-F-010 | The harness shall produce a concise structured review summary suitable for downstream consumption by the UI or other clients. | The review summary is a contract between harness and UI, and must be machine-consumable. | Proposed |
| FLH-F-011 | The harness shall emit standardized, downloadable artifacts including STEP, GLB, render sheet, and model source when available. | Artifacts are the durable output of a run and must be independently consumable. | Proposed |
| FLH-F-012 | The harness shall record and expose tool-call history, subagent-call history, and intermediate traces for each run. | Traceability is required for debugging, review, and UI disclosure. | Proposed |
| FLH-F-013 | The harness shall provide a high-level operator CLI for application lifecycle management. | The architecture explicitly defines a separate Formloop operator CLI. | Proposed |
| FLH-F-014 | The operator CLI shall support UI start, stop, and status operations. | Application lifecycle management is part of the agreed boundary for Formloop. | Proposed |
| FLH-F-015 | The operator CLI shall support single-run execution outside the UI. | The system should support individual queries outside the interactive app surface. | Proposed |
| FLH-F-016 | The harness shall support developer eval runs over one or more datasets with known ground-truth geometry. | Developer evals are a first-class project capability. | Proposed |
| FLH-F-017 | The harness's evals shall combine deterministic calculators and agent eval judges. | The project explicitly requires both objective metrics and higher-level judge assessments. | Proposed |
| FLH-F-018 | The harness's evals shall support tool-using agent judges where useful for multi-step assessments such as dimensional compliance. | The user explicitly allowed agentic judges in eval routines. | Proposed |
| FLH-F-019 | The harness's evals shall generate per-case outputs and aggregate batch outputs. | Both detailed failure analysis and regression summaries are required. | Proposed |
| FLH-F-020 | The harness shall support CI-triggered batch eval execution and reporting. | CI regression detection is part of the agreed evaluation model. | Proposed |
| FLH-F-021 | The harness shall manage standardized artifact types across design runs, internal review runs, and eval runs. | Shared artifact conventions are necessary for UI, tooling, and CI interoperability. | Proposed |
| FLH-F-022 | The harness shall support a skill system that provides reusable operational knowledge to agents. | Skills are a central design element for keeping prompts cleaner and more reusable. | Proposed |
| FLH-F-023 | The harness's skill system shall comply with the open Agent Skills standard as defined at [agentskills.io](https://agentskills.io/home) and described in OpenAI's tools/skills guide ([developers.openai.com](https://developers.openai.com/api/docs/guides/tools-skills)). | Alignment with an open standard preserves interoperability across agent platforms and reduces lock-in to any single vendor's skill format. | Proposed |
| FLH-F-024 | The harness shall allow the manager agent to request external research when required to complete ambiguous or under-specified designs. | The Design Researcher role exists specifically to fill this gap. | Proposed |
| FLH-F-025 | The harness shall keep manufacturing or slicing validation outside the core design loop in v1. | The project explicitly treats 3D printing validation as optional future scope. | Proposed |
| FLH-F-026 | The harness shall expose a stable HTTP programmatic interface through which clients can create runs, poll run snapshots and events, submit clarification answers, and retrieve run state and artifacts. | The UI is a separate build and must integrate with the harness through a clean contract. | Proposed |
| FLH-F-027 | The harness's internal review loop shall supply the rendered PNG images of the latest candidate to review or judge LLMs as multimodal image inputs, and shall drive the review by comparing those rendered images against (i) the normalized fit/form/function specification and (ii) any user-provided reference image. | Visual review is what actually closes the loop. | Proposed |
| FLH-F-028 | The harness shall manage the rendered PNG files as durable, addressable artifacts: persisted per run, versioned per revision, and referenceable by review steps, eval steps, and the UI. | The same rendered images are consumed by the review loop, by evals, and by the UI. | Proposed |
| FLH-F-029 | The harness shall use the OpenAI Agents SDK as its primary agent orchestration framework. | This is the chosen primary execution framework for the harness. | Proposed |
| FLH-F-030 | OpenAI-backed runs shall use the OpenAI Responses model path by default. | The Responses path is the preferred OpenAI integration path for the chosen agent framework. | Proposed |
| FLH-F-031 | The harness shall support Anthropic-backed runs via the OpenAI Agents SDK LiteLLM provider path. | Anthropic support is required while keeping the primary orchestration framework consistent. | Proposed |
| FLH-F-032 | The harness shall support checked-in named run profiles for at least `normal`, `dev_test`, and `eval`. | A small set of named profiles keeps configuration simple while supporting different cost/quality modes. | Proposed |
| FLH-F-033 | The `normal` profile shall default to OpenAI `gpt-5.4` with high reasoning. | Normal execution should prioritize output quality. | Proposed |
| FLH-F-034 | The `dev_test` profile shall default to a low-cost GPT-5-family model intended for plumbing validation, with `gpt-5.4-nano` as the initial target subject to model availability. | Developer or test execution should validate wiring without incurring unnecessary cost. | Proposed |
| FLH-F-035 | The `eval` profile shall default to OpenAI `gpt-5.4` with high reasoning. | Eval execution should default to high-fidelity benchmarking behavior. | Proposed |
| FLH-F-036 | The harness configuration surface shall expose a normalized thinking setting such as `low`, `medium`, and `high`, with provider-specific mappings handled internally. | A shared reasoning control keeps configuration simple across OpenAI and Anthropic. | Proposed |
| FLH-F-037 | The harness shall keep other model parameters on sensible defaults unless a requirement explicitly promotes one into the supported configuration surface. | The user wants a small, maintainable configuration surface rather than a large parameter matrix. | Proposed |
| FLH-F-038 | The harness shall support run-level provider and model selection, with per-agent exceptions allowed only where a requirement explicitly calls for them. | Run-level selection is the chosen default complexity boundary. | Proposed |
| FLH-F-039 | The manager agent shall attempt a first CAD iteration by default. | The manager should bias toward progress rather than unnecessary clarification. | Proposed |
| FLH-F-040 | The manager agent shall ask clarifying questions before first-pass CAD generation only when critical gaps make a credible initial model impossible. | Clarification should block only when it materially prevents a believable first iteration. | Proposed |
| FLH-F-041 | For the purpose of first-pass generation, critical gaps shall include missing information about core function, mandatory interfaces, must-hit dimensions or tolerances, or other blocking constraints. | The clarification threshold must be explicit enough to implement and test. | Proposed |
| FLH-F-042 | When the manager agent proceeds without clarification, it shall record explicit assumptions in structured run state. | Assumption traceability is required when the system moves forward under ambiguity. | Proposed |
| FLH-F-043 | The CAD Designer shall operate with the persona and decision quality expected of a Mechanical Design Engineer, prioritizing standards-aware, manufacturable, and spec-grounded modeling. | The CAD Designer is expected to behave like an engineering specialist rather than a generic code generator. | Proposed |
| FLH-F-044 | The CAD Designer shall proactively invoke the Design Researcher when named parts, mechanisms, conventions, or standards imply factual external knowledge that should guide the design. | Named engineering terms often imply external standards and conventions that should inform the design. | Proposed |
| FLH-F-045 | The operator CLI shall support profile-aware execution for `formloop run`, `formloop eval run`, and `formloop doctor`. | Named profiles must be usable through the primary operator surfaces. | Proposed |
| FLH-F-046 | `formloop run` shall support `--interactive` and `--no-interactive`; the CLI default shall be `--no-interactive`, while UI-initiated runs shall default to interactive behavior. | Clarification behavior must differ cleanly between automated and user-facing entry points. | Proposed |
| FLH-F-047 | In non-interactive mode, critical-gap detection shall move the run cleanly into `blocked_on_clarification` with a structured clarification event rather than silently failing or producing a low-confidence first pass. | Non-interactive flows still need explicit system-boundary feedback. | Proposed |
| FLH-F-048 | In interactive mode, clarification answers shall resume the blocked run in place rather than starting a replacement run. | Clarification should preserve run traceability and in-progress state. | Proposed |
| FLH-F-049 | The harness shall capture the effective run profile, provider, model, thinking level, and interaction mode in per-run and per-revision metadata. | Effective runtime configuration is a core part of traceability and debugging. | Proposed |
| FLH-F-050 | The harness shall record structured clarification events and structured assumption records in run state. | Clarification behavior and assumption-taking must be inspectable after the fact. | Proposed |
| FLH-F-051 | The harness shall model top-level execution as `run > revision`. | The user wants a single persistent design thread concept while still preserving iteration boundaries. | Proposed |
| FLH-F-052 | A run shall be the single persistent state container for one part, project, or eval case across autonomous execution, clarification pauses, and later user-directed modifications. | This keeps the lifecycle model simple while preserving continuity across the full design experience. | Proposed |
| FLH-F-053 | A revision shall exist only when a candidate artifact bundle has been generated and persisted within a run. | Revisions should track concrete candidate iterations rather than every spec or dialogue change. | Proposed |
| FLH-F-054 | Run status values shall be exactly `active`, `blocked_on_clarification`, `completed`, `terminated_at_cap`, and `failed`. | Callers need a stable finite state model for branching and display. | Proposed |
| FLH-F-055 | The run-polling contract shall return both a materialized run snapshot and an append-only structured event log. | Clients need both current state and inspectable progress history without streaming. | Proposed |
| FLH-F-056 | `formloop run` shall accept `--reference-image <path>` and the harness shall copy that image into the run's artifact folder and link it to the run record. | CLI parity is required for reference-image-assisted flows. | Proposed |
| FLH-F-057 | The harness shall accept only one optional reference image per request in v1, and supported formats shall be PNG and JPEG. | This keeps initial UI, CLI, schema, and review contracts intentionally small. | Proposed |
| FLH-F-058 | The harness shall persist a complete revision bundle before proceeding to any subsequent revision. | The user explicitly wants something inspectable saved at each loop boundary. | Proposed |
| FLH-F-059 | When configured turn or revision caps are approached, the harness shall reserve landing budget to persist the best available artifact bundle and emit a partial review or terminal summary rather than exhausting the budget abruptly. | Cap behavior should land gracefully instead of burning tokens and returning nothing useful. | Proposed |
| FLH-F-060 | `formloop doctor` shall validate required keys, the selected profile, provider or model resolvability, missing dependency or configuration issues, and `cad-cli` compatibility before first run. | Early validation reduces avoidable failures during development and normal use. | Proposed |
| FLH-F-061 | A run may transition from `blocked_on_clarification` or `completed` back to `active` when the user supplies clarification or follow-up modification input. | The run is intentionally long-lived and reopenable over time. | Proposed |
| FLH-F-062 | The run shall retain status history so prior blocked, completed, or capped outcomes remain inspectable after a reopen. | Reopenability must not erase earlier outcomes or make audit history ambiguous. | Proposed |
| FLH-F-063 | Revision ordinals shall be monotonic within a run and shall not reset after clarification, reopen, or later user-directed modifications. | Revision numbering must remain stable and intuitive across the full run lifetime. | Proposed |
| FLH-F-064 | Clarification, research, or spec cleanup alone shall not create a revision. | Revisions should correspond only to persisted candidate geometry iterations. | Proposed |

### Non-functional requirements

| ID         | Requirement | Rationale | Status   |
| ---------- | ----------- | --------- | -------- |
| FLH-NF-001 | The harness shall enable maximal autonomy while maintaining safety and reliability. | Safety and reliability are explicit project objectives. | Proposed |
| FLH-NF-002 | The harness shall emit intermediate progress updates during multi-step runs in a form suitable for polling consumption as structured snapshots plus append-only events, not as a streaming-only contract. | Progress visibility is required by the UI and by operator tooling, but the programmatic contract is explicitly non-streaming in v1. | Proposed |
| FLH-NF-003 | The harness shall preserve artifact traceability across runs, revisions, review steps, status changes, and eval results. | Traceability is a cross-cutting design objective. | Proposed |
| FLH-NF-004 | The harness shall support reproducible eval execution for regression tracking. | Developer evals must be usable as a stable quality bar over time. | Proposed |
| FLH-NF-005 | The harness shall be operable in a headless environment through its CLI and CI integrations even if the UI is not running. | Automation and CI must not depend on an interactive UI session. | Proposed |
| FLH-NF-006 | The harness shall keep the internal design loop and developer eval loop conceptually distinct in both implementation and reporting. | The user explicitly requested clarity between these two modes. | Proposed |
| FLH-NF-007 | The harness shall expose enough logs and structured data to debug failures in design runs and eval runs. | High-quality iteration depends on diagnosability. | Proposed |
| FLH-NF-008 | The harness should minimize unnecessary context growth by using specialist boundaries and skills intentionally. | Context cleanliness is one of the explicit reasons for the subagent and skill architecture. | Proposed |
| FLH-NF-009 | The harness shall support CI reporting on push to `main` and a smaller smoke path for pull requests. | This is part of the agreed developer workflow. | Proposed |
| FLH-NF-010 | The harness shall provide provider-agnostic run tracing and observability across supported model providers. | Traceability must remain available even when multiple providers are supported. | Proposed |
| FLH-NF-011 | The harness shall target near-full parity for core harness flows across OpenAI and Anthropic-backed runs, while not promising identical provider-specific behavior for every advanced feature. | The user wants strong cross-provider support without overpromising adapter-dependent behavior. | Proposed |

### Design and technical constraint requirements

| ID        | Requirement | Rationale | Status   |
| --------- | ----------- | --------- | -------- |
| FLH-D-001 | The harness shall use `cad-cli` as its deterministic CAD tool substrate rather than embedding those responsibilities directly. | The architecture deliberately separates deterministic tool execution from the application harness. | Proposed |
| FLH-D-002 | The harness shall use build123d as the primary modeling backend exposed through its design workflows. | This is a core technical decision for the project. | Proposed |
| FLH-D-003 | The harness shall produce Blender-rendered GLB outputs as the standard presentation geometry artifact delivered to downstream consumers. | GLB is the agreed interchange format for UI viewing and downstream presentation. | Proposed |
| FLH-D-004 | The harness shall treat STEP as the authoritative geometry artifact in its internal state and eval workflows. | STEP is the agreed source-of-truth artifact for CAD and comparison. | Proposed |
| FLH-D-005 | The harness shall expose a centralized internal runtime abstraction for CLI execution, constrained Python execution, artifact reads, and artifact writes. | The agreed harness uses a constrained runtime rather than a broker service. | Proposed |
| FLH-D-006 | The harness shall not require a separate tool broker service in v1. | The user explicitly rejected a broker-based design for the initial architecture. | Proposed |
| FLH-D-007 | The harness shall represent the current design state explicitly rather than reconstructing it from raw chat alone. | The UI and manager both depend on a normalized current state object. | Proposed |
| FLH-D-008 | The harness shall keep internal review artifacts and eval artifacts distinct, even when some underlying tools are shared. | The project requires clarity between internal review and developer evaluation. | Proposed |
| FLH-D-009 | The harness shall support standardized output schemas for deterministic metrics and judge outputs. | Evals require consistent aggregation and CI reporting. | Proposed |
| FLH-D-010 | The harness shall reserve an optional future integration point for printability validation but shall not make it a core release requirement. | 3D printing validation is intentionally deferred from the core project boundary. | Proposed |
| FLH-D-011 | The harness shall maintain a checked-in, non-secret configuration file for named run profiles and runtime defaults. | The chosen configuration model separates shareable defaults from secrets. | Proposed |
| FLH-D-012 | Secrets shall be supplied through environment variables only and shall not be committed to the repository. | This keeps secret handling simple and safe for both development and normal execution. | Proposed |
| FLH-D-013 | Environment variable support shall include at minimum `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` when the corresponding providers are enabled. | The initial provider set requires explicit key contracts. | Proposed |
| FLH-D-014 | The harness shall normalize provider-specific thinking controls behind a shared configuration abstraction rather than exposing provider-specific reasoning parameters directly in the primary config surface. | A small cross-provider control surface is easier to use and maintain. | Proposed |
| FLH-D-015 | The programmatic interface shall be HTTP-only in v1 and shall use asynchronous job semantics rather than streaming transports. | The agreed v1 contract is polling-based HTTP, not a streaming protocol. | Proposed |
| FLH-D-016 | The HTTP interface shall use HTTP status codes for request-validation failures, authentication failures, and server faults, while run outcomes shall be represented in run status and event payloads. | Transport errors and run outcomes need cleanly separated contracts. | Proposed |
| FLH-D-017 | The runtime abstraction shall capture and parse structured JSON from `cad-cli` stdout for each command it invokes. | `cad-cli` is treated as a structured deterministic contract rather than a text-scraping interface. | Proposed |
| FLH-D-018 | The repository shall declare one supported `cad-cli` release in checked-in config, and each versioned skill that invokes `cad-cli` shall declare the command stdout fields it depends on. | Compatibility needs both a repo-wide target and per-skill field expectations. | Proposed |
| FLH-D-019 | The harness shall check in versioned JSON Schemas for its primary persisted state, API, and report contracts before implementation begins. | JSON Schema is the chosen canonical contract source for v1. | Proposed |
| FLH-D-020 | The initial checked-in schema set shall include run, revision, artifact manifest, run snapshot, progress event, clarification event, recorded assumption, review summary, deterministic metrics output, judge output, run-create request and response, clarification-response request and response, and artifact listing or download metadata. | The initial surface needs explicit machine-readable contracts before scaffolding. | Proposed |
| FLH-D-021 | The stable runtime filesystem convention shall be one run folder containing stable run metadata, event history, input artifacts, and nested revision folders that each contain the complete persisted revision bundle. | Shared directory structure is needed across UI, CLI, CI, and eval workflows. | Proposed |
| FLH-D-022 | The default complete revision bundle shall include STEP, GLB, per-view PNGs, render sheet PNG, revision metadata JSON, and artifact manifest JSON; after review completes it shall also include review summary JSON and review notes or output; model source snapshots and research artifacts are optional when available. | Revision completeness must be concrete enough to validate and test. | Proposed |
| FLH-D-023 | The initial cap defaults shall be profile-configurable and shall start as `normal`: 16 manager turns, 8 specialist turns, 3 revisions; `dev_test`: 6 manager turns, 3 specialist turns, 1 revision; `eval`: 12 manager turns, 6 specialist turns, 1 revision. | Cost control needs explicit default limits before implementation. | Proposed |
| FLH-D-024 | The eval LLM judge shall score `requirement_adherence` and `feature_coverage` independently on a `0..4` scale, shall report an equal-weight average aggregate, and shall include confidence on a `0.0..1.0` scale. | The eval judge contract must be stable and machine-readable. | Proposed |
| FLH-D-025 | The deterministic geometry comparison contract shall compute and report shared volume, only-in-candidate volume, only-in-ground-truth volume, and composite IoU ratio. | The required deterministic metric needs a precise v1 definition. | Proposed |
| FLH-D-026 | Eval judge prompts shall explicitly instruct the judge to ignore background color, lighting, edge rendering style, and geometry color, and to evaluate shape, geometry, and feature content only. | Visual-eval prompts need explicit guardrails to reduce irrelevant variance. | Proposed |

### Validation and UAT requirements

| ID        | Requirement | Rationale | Status   |
| --------- | ----------- | --------- | -------- |
| FLH-V-001 | The harness shall maintain strong unit-test coverage over deterministic logic, schema and config parsing, and run-state serialization behavior. | Deterministic logic and contracts should be validated at the smallest practical scope. | Proposed |
| FLH-V-002 | The harness shall maintain integration coverage for agent orchestration, runtime and tool boundaries, persistence, HTTP API behavior, and artifact and report generation. | Cross-boundary behavior is central to the product and cannot be proven by unit tests alone. | Proposed |
| FLH-V-003 | The harness shall run critical smoke tests for end-to-end operator flows on pull requests. | Pull request validation should quickly catch major regressions in the most important flows. | Proposed |
| FLH-V-004 | The harness shall run broader eval and user-acceptance coverage on `main` and before release readiness decisions. | Release confidence requires broader evidence than the pull request smoke path. | Proposed |
| FLH-V-005 | The harness requirements shall maintain an explicit catalog of critical user and operator UAT scenarios with acceptance criteria. | Important flows should be defined up front so implementation and validation stay aligned. | Proposed |
| FLH-V-006 | Acceptance criteria for critical flows shall require system-boundary evidence such as surfaced clarification behavior, run continuity across reopen, profile selection, artifact generation, review outputs, recorded runtime metadata, and API or CLI responses. | The project definition of done requires evidence from the real workflow boundary. | Proposed |
| FLH-V-007 | The harness shall validate both interactive and non-interactive clarification paths. | Clarification behavior is now an explicit product contract, not an implementation detail. | Proposed |
| FLH-V-008 | The harness shall validate `cad-cli` compatibility and schema-contract conformance as part of preflight and integration coverage. | The system depends on stable structured contracts across tools and persisted state. | Proposed |
| FLH-V-009 | The harness shall validate cap-landed behavior, ensuring that terminal-at-cap runs still surface the best available persisted artifacts and partial summaries. | Graceful landing at limits is part of the required user experience. | Proposed |

### Configuration and runtime contract

The harness configuration baseline is intentionally small:

- The checked-in non-secret configuration file shall live at the repo root as `formloop.harness.toml`.
- The initial named profiles are `normal`, `dev_test`, and `eval`.
- Local development secrets should be loaded from a repo-root `.env.local` file into environment variables at process start; `.env.local` shall remain untracked.
- `.gitignore` and `.env.example` are the canonical tracked secret-posture references for the repo and should remain aligned with the requirements.
- CI and regular deployed execution shall provide the same secrets through environment variables rather than a checked-in file.
- The minimum environment variable contract is `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`, with provider-specific keys only required when the corresponding provider is enabled.

The initial profile defaults are:

| Profile | Default provider path | Default model | Default thinking | Purpose |
| ------- | --------------------- | ------------- | ---------------- | ------- |
| `normal` | OpenAI Responses | `gpt-5.4` | `high` | Normal user-facing execution where design quality matters most. |
| `dev_test` | OpenAI Responses | `gpt-5.4-nano` | `low` | Cheap developer plumbing checks and smoke validation. |
| `eval` | OpenAI Responses | `gpt-5.4` | `high` | Higher-fidelity eval and benchmarking runs unless an alternate provider is intentionally under test. |

The initial cap defaults are:

| Profile | Manager turns | Specialist turns | Max revisions |
| ------- | ------------- | ---------------- | ------------- |
| `normal` | `16` | `8` | `3` |
| `dev_test` | `6` | `3` | `1` |
| `eval` | `12` | `6` | `1` |

The stable run-state contract shall include at minimum:

- run identifier
- revision identifiers
- effective profile
- effective provider path
- effective model
- effective thinking level
- effective interaction mode
- current status
- status history
- structured clarification events
- structured recorded assumptions
- artifact manifest references

The minimum HTTP operation set shall include:

- create run
- poll run snapshot and events
- submit clarification answer to blocked run
- retrieve artifacts and review outputs

### Schema contract appendix

Before implementation begins, the repository shall check in versioned JSON Schemas organized as one file per schema under `schemas/`.

This first pass shall fully define only the core contracts below. The remaining listed contracts shall stay intentionally simple as named placeholder schemas with short purpose notes until implementation pressure requires more detail.

#### Core schemas to define now

`run`

- Purpose: the single long-lived design or eval thread for one part, project, or benchmark case.
- Minimum fields:
  - `run_id`
  - `title` or short request label
  - `status`
  - `status_history`
  - `created_at`
  - `updated_at`
  - `current_spec`
  - `input_summary`
  - `reference_image` optional
  - `assumptions`
  - `clarifications`
  - `revisions`
  - `current_revision_id` optional
  - effective runtime metadata: profile, provider, model, thinking, interaction mode
- Required behavior notes:
  - the run may reopen from `blocked_on_clarification` or `completed` back to `active`
  - reopening appends to `status_history` instead of overwriting prior outcomes

`revision`

- Purpose: one persisted candidate iteration inside a run.
- Minimum fields:
  - `revision_id`
  - `ordinal`
  - `created_at`
  - `trigger`
  - `spec_snapshot`
  - `artifact_manifest_path`
  - `review_summary_path` optional until review completes
  - `status`
- Required behavior notes:
  - a revision is created only after a candidate artifact bundle is generated and persisted
  - revision ordinals are monotonic within a run and do not reset after clarification or reopen

`artifact-manifest`

- Purpose: the stable listing of revision artifacts by role.
- Minimum fields:
  - artifact entries keyed by stable role
  - `path`
  - `format`
  - `required` or optional marker

`review-summary`

- Purpose: the concise structured result of internal review for one revision.
- Minimum fields:
  - `decision` with `pass` or `revise`
  - `confidence`
  - `key_findings`
  - `suspect_or_missing_features`
  - `suspect_dimensions_to_recheck`
  - `revision_instructions`

`run-snapshot`

- Purpose: the polling-friendly materialized view of current run state.
- Minimum fields:
  - `run_id`
  - current `status`
  - current spec summary
  - latest revision pointer
  - latest review summary pointer
  - artifact summary
  - append-only event cursor or last event reference

#### Placeholder schemas to name now

The repository shall also check in placeholder schemas for the following contracts, with a short purpose note in the appendix and one schema file per contract:

- `progress-event`
  - Purpose: append-only status and activity updates emitted during a run.
- `clarification-event`
  - Purpose: the structured record of a clarification request and any eventual answer.
- `recorded-assumption`
  - Purpose: a structured assumption the system records when proceeding under ambiguity.
- `deterministic-metrics-output`
  - Purpose: the persisted output of deterministic eval and comparison metrics.
- `judge-output`
  - Purpose: the persisted output of the qualitative eval judge.
- `run-create-request`
  - Purpose: the minimum HTTP payload for starting a new run.
- `run-create-response`
  - Purpose: the minimum HTTP payload returned when a run is created.
- `clarification-response-request`
  - Purpose: the minimum HTTP payload for submitting a clarification answer into an existing run.
- `clarification-response-response`
  - Purpose: the minimum HTTP payload acknowledging a clarification answer and resumed run state.
- `artifact-listing-download-metadata`
  - Purpose: the metadata contract for browsing and retrieving run and revision artifacts.

### Filesystem and repo layout appendix

The runtime artifact tree shall live under `var/runs/`. This is generated runtime state: it should be human-inspectable and discoverable, but it is not core source code.

The default runtime tree shall be:

- `var/runs/<run-id>/run.json`
- `var/runs/<run-id>/events.jsonl`
- `var/runs/<run-id>/inputs/`
- `var/runs/<run-id>/revisions/rev-001/`

The default revision bundle under each revision folder shall be:

- `revision.json`
- `artifact-manifest.json`
- `step.step`
- `model.glb`
- `render-sheet.png`
- `views/`
- `review-summary.json` after review
- `review-notes.*` after review
- optional `source/`
- optional `research/`

The revision bundle completeness rule is:

- required before a subsequent revision may begin: `revision.json`, `artifact-manifest.json`, `step.step`, `model.glb`, `render-sheet.png`, and `views/`
- required after review completes: `review-summary.json` and `review-notes.*`
- optional when available: `source/` and `research/`

### Repo-root layout appendix

To keep the repository intuitive to someone unfamiliar with the codebase, the top-level project layout should stay simple and human-readable:

- `src/formloop/` - primary application code for harness, CLI, runtime, eval orchestration, and shared domain logic
- `ui/` - browser UI that talks to the harness HTTP API
- `schemas/` - one JSON Schema file per checked-in contract
- `tests/` - unit, integration, and smoke tests
- `datasets/` - eval datasets and related fixtures
- `skills/` - checked-in skills used by the harness
- `docs/` - secondary docs and design notes; keep `README.md`, `SPEC.md`, and requirements files at the repo root
- `scripts/` - developer tooling and helper scripts
- `var/runs/` - generated run state and artifacts for local and development execution

### UAT scenarios and acceptance criteria

The following user and operator flows are mandatory UAT coverage for the harness:

| ID | Scenario | Acceptance criteria | Required evidence |
| -- | -------- | ------------------- | ----------------- |
| UAT-001 | Fully specified new design request | A first candidate is generated without clarification and the run surfaces artifacts plus a review summary. | Run record, generated artifacts, review summary, effective profile metadata. |
| UAT-002 | Critically underspecified request in interactive mode | The manager blocks first-pass CAD generation, emits a clarification event, and resumes the same run after the answer is submitted. | Run record, clarification event, status-history transition back to `active`, post-resume artifacts. |
| UAT-003 | Critically underspecified request in non-interactive mode | The run moves cleanly into `blocked_on_clarification` and does not silently generate a weak first pass. | CLI or API response, current run status, structured clarification event. |
| UAT-004 | Partially ambiguous request | The manager proceeds with a first pass and records explicit assumptions instead of blocking. | Generated candidate, structured assumptions, review summary, effective profile metadata. |
| UAT-005 | Standards-backed request | The system invokes or records relevant external research before or during modeling when named standards, mechanisms, or commodity parts are implicated. | Research trace, cited factual findings, updated spec or modeling inputs. |
| UAT-006 | Reference-image-assisted request | The internal review loop consumes one PNG or JPEG reference image alongside rendered model outputs. | Copied reference image artifact, run linkage, review trace, review summary with image-informed findings. |
| UAT-007 | Revision after internal review | The Review Specialist requests revision feedback, the current revision bundle is persisted completely, and a later iteration is generated. | Review finding requesting revision, persisted prior revision bundle, subsequent revision artifacts, updated review summary. |
| UAT-008 | Run continuity across follow-up work | A later user follow-up after a prior completion reopens the same run, preserves prior outcomes in status history, and continues revision numbering without reset. | Run record, status-history transitions, linked revision history, surfaced continuity in API or UI state. |
| UAT-009 | Profile-aware run execution | `formloop run` succeeds with both the `normal` profile and an alternate Anthropic-backed profile. | CLI invocation record, effective profile/provider/model metadata, successful run outputs. |
| UAT-010 | Eval execution | `formloop eval run` produces deterministic metrics, judge outputs, equal-weight aggregate scoring, and aggregate reporting artifacts. | Per-case outputs, aggregate summary, judge outputs JSON, deterministic metrics JSON. |
| UAT-011 | Doctor validation | `formloop doctor` fails cleanly when required keys are missing and passes when configuration, schema, and `cad-cli` compatibility are valid. | CLI output for failure and success cases, validation details for keys, profiles, schemas, and tool compatibility. |
| UAT-012 | Polling-based API progress | The HTTP API supports async run creation and polling of run snapshot plus append-only event log without a streaming dependency. | API responses for create and poll operations, event log examples, run snapshot payloads. |
| UAT-013 | Graceful landing at cap | When a configured cap is reached, the run moves to `terminated_at_cap` while surfacing the best available persisted artifact set and partial summary. | Run record, persisted artifacts, partial review or terminal summary, cap-related event trace. |
| UAT-014 | End-to-end traceability | Traceability is preserved across run input, spec, research, artifacts, review, status history, and final output. | Inspectable run record tying together spec state, research, artifacts, review results, status transitions, and effective runtime metadata. |

### Development auth setup

Before implementation work begins, local development should be initialized as follows:

1. Create `/Users/jdegregorio/Repos/formloop/.env.local`.
2. Set at minimum:
   - `OPENAI_API_KEY=...`
   - `ANTHROPIC_API_KEY=...`
3. Keep provider and profile selection in `formloop.harness.toml`, not in `.env.local`.
4. Keep `.env.local` untracked and use `.env.example` as the tracked template for required secret names only.

These requirements are meant to be a working baseline. The most important maintenance rule is simple: **keep the Status column current as development progresses**, so the spec remains a living control document rather than a one-time design artifact.
