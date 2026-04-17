## Requirements specification for Formloop — Agent Harness

**Scope**: This document covers requirements for the Formloop agent harness: the manager/specialist agents, the constrained execution runtime, the internal design-loop review, developer eval orchestration, the operator CLI, dataset management, run history, and artifact plumbing. UI-facing requirements are tracked separately in [REQUIREMENTS_UI.md](REQUIREMENTS_UI.md).

**Important**: Keep each requirement status up to date during development. Include comments that reference requirements in-code wherever possible.

### Functional requirements

| ID        | Requirement                                                                                                                                                                              | Rationale                                                                                     | Status   |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | -------- |
| FLH-F-001 | The harness shall maintain a normalized current fit/form/function specification for the active design.                                                                                   | The current spec is a core user-facing and agent-facing object in the agreed design.          | Proposed |
| FLH-F-002 | The harness shall provide a manager agent that coordinates the active run and delegates to specialist agents.                                                                            | The agreed architecture uses a manager-plus-specialists harness.                              | Proposed |
| FLH-F-003 | The harness shall provide at minimum the specialist roles CAD Designer, Design Researcher, Render Specialist, Review Specialist, and Eval Specialist.                                    | These are the agreed initial specialist boundaries.                                           | Proposed |
| FLH-F-004 | The harness shall support an internal review loop for normal design runs where no ground-truth geometry is available.                                                                    | The project explicitly distinguishes internal design-loop review from developer evals.        | Proposed |
| FLH-F-005 | The harness's internal review loop shall assess the latest candidate against the normalized spec, rendered outputs, deterministic inspections, and optional user-provided reference images. | This is the agreed basis for closed-loop design review without ground truth.                  | Proposed |
| FLH-F-006 | The harness shall support deterministic measurement and inspection requests inside the internal review loop.                                                                             | Internal review requires concrete checks, not only visual judgment.                           | Proposed |
| FLH-F-007 | The harness shall support reference-image review as a closed-loop review tool when the user provides a reference image.                                                                  | Reference-image comparison is an explicitly requested review capability.                      | Proposed |
| FLH-F-008 | The harness shall allow the Review Specialist to request further revision from the CAD Designer when the current candidate is not acceptable.                                            | The review loop must be able to drive iterative improvement.                                  | Proposed |
| FLH-F-009 | The harness shall generate and retain the standard multi-view rendered images of the latest candidate geometry for use in the closed-loop review process.                                | Rendered images remain the primary visual signal for agent-driven review, even when human-facing UIs move to interactive GLB viewing. | Proposed |
| FLH-F-010 | The harness shall produce a concise structured review summary suitable for downstream consumption by the UI or other clients.                                                            | The review summary is a contract between harness and UI, and must be machine-consumable.      | Proposed |
| FLH-F-011 | The harness shall emit standardized, downloadable artifacts including STEP, GLB, render sheet, and model source when available.                                                          | Artifacts are the durable output of a run and must be independently consumable.               | Proposed |
| FLH-F-012 | The harness shall record and expose tool-call history, subagent-call history, and intermediate traces for each run.                                                                      | Traceability is required for debugging, review, and UI disclosure.                            | Proposed |
| FLH-F-013 | The harness shall provide a high-level operator CLI for application lifecycle management.                                                                                                | The architecture explicitly defines a separate Formloop operator CLI.                         | Proposed |
| FLH-F-014 | The operator CLI shall support UI start, stop, and status operations.                                                                                                                    | Application lifecycle management is part of the agreed boundary for Formloop.                 | Proposed |
| FLH-F-015 | The operator CLI shall support single-run execution outside the UI.                                                                                                                      | The system should support individual queries outside the interactive app surface.             | Proposed |
| FLH-F-016 | The harness shall support developer eval runs over one or more datasets with known ground-truth geometry.                                                                                | Developer evals are a first-class project capability.                                         | Proposed |
| FLH-F-017 | The harness's evals shall combine deterministic calculators and agent eval judges.                                                                                                       | The project explicitly requires both objective metrics and higher-level judge assessments.    | Proposed |
| FLH-F-018 | The harness's evals shall support tool-using agent judges where useful for multi-step assessments such as dimensional compliance.                                                        | The user explicitly allowed agentic judges in eval routines.                                  | Proposed |
| FLH-F-019 | The harness's evals shall generate per-case outputs and aggregate batch outputs.                                                                                                         | Both detailed failure analysis and regression summaries are required.                         | Proposed |
| FLH-F-020 | The harness shall support CI-triggered batch eval execution and reporting.                                                                                                               | CI regression detection is part of the agreed evaluation model.                               | Proposed |
| FLH-F-021 | The harness shall manage standardized artifact types across design runs, internal review runs, and eval runs.                                                                            | Shared artifact conventions are necessary for UI, tooling, and CI interoperability.           | Proposed |
| FLH-F-022 | The harness shall support a skill system that provides reusable operational knowledge to agents.                                                                                         | Skills are a central design element for keeping prompts cleaner and more reusable.            | Proposed |
| FLH-F-023 | The harness's skill system shall comply with the open Agent Skills standard as defined at [agentskills.io](https://agentskills.io/home) and described in OpenAI's tools/skills guide ([developers.openai.com](https://developers.openai.com/api/docs/guides/tools-skills)). | Alignment with an open standard preserves interoperability across agent platforms and reduces lock-in to any single vendor's skill format. | Proposed |
| FLH-F-024 | The harness shall allow the manager agent to request external research when required to complete ambiguous or under-specified designs.                                                   | The Design Researcher role exists specifically to fill this gap.                              | Proposed |
| FLH-F-025 | The harness shall keep manufacturing or slicing validation outside the core design loop in v1.                                                                                           | The project explicitly treats 3D printing validation as optional future scope.                | Proposed |
| FLH-F-026 | The harness shall expose a stable programmatic interface (e.g., HTTP or equivalent) through which the UI can submit requests, stream progress, and retrieve run state and artifacts.    | The UI is a separate build and must integrate with the harness through a clean contract.     | Proposed |
| FLH-F-027 | The harness's internal review loop shall supply the rendered PNG images of the latest candidate to review/judge LLMs as multimodal image inputs, and shall drive the review by comparing those rendered images against (i) the normalized fit/form/function specification and (ii) any user-provided reference image. | Visual review is what actually closes the loop — the review agent cannot make a grounded judgment without the rendered geometry in front of it, and both the spec and the reference image are first-class points of comparison. | Proposed |
| FLH-F-028 | The harness shall manage the rendered PNG files as durable, addressable artifacts: persisted per run, versioned per revision, and referenceable by review steps, eval steps, and the UI. | The same rendered images are consumed by the review loop, by evals, and by the UI, so they must be a durable shared artifact rather than transient in-memory buffers. | Proposed |
| FLH-F-029 | The harness shall use the OpenAI Agents SDK as its primary agent orchestration framework. | This is the chosen primary execution framework for the harness. | Proposed |
| FLH-F-030 | OpenAI-backed runs shall use the OpenAI Responses model path by default. | The Responses path is the preferred OpenAI integration path for the chosen agent framework. | Proposed |
| FLH-F-031 | The harness shall support Anthropic-backed runs via the OpenAI Agents SDK LiteLLM provider path. | Anthropic support is required while keeping the primary orchestration framework consistent. | Proposed |
| FLH-F-032 | The harness shall support checked-in named run profiles for at least `normal`, `dev_test`, and `eval`. | A small set of named profiles keeps configuration simple while supporting different cost/quality modes. | Proposed |
| FLH-F-033 | The `normal` profile shall default to OpenAI `gpt-5.4` with high reasoning. | Normal execution should prioritize output quality. | Proposed |
| FLH-F-034 | The `dev_test` profile shall default to a low-cost GPT-5-family model intended for plumbing validation, with `gpt-5.4-nano` as the initial target subject to model availability. | Developer/test execution should validate wiring without incurring unnecessary cost. | Proposed |
| FLH-F-035 | The harness configuration surface shall expose a normalized thinking setting such as `low`, `medium`, and `high`, with provider-specific mappings handled internally. | A shared reasoning control keeps configuration simple across OpenAI and Anthropic. | Proposed |
| FLH-F-036 | The harness shall keep other model parameters on sensible defaults unless a requirement explicitly promotes one into the supported configuration surface. | The user wants a small, maintainable configuration surface rather than a large parameter matrix. | Proposed |
| FLH-F-037 | The harness shall support run-level provider/model selection, with per-agent exceptions allowed only where a requirement explicitly calls for them. | Run-level selection is the chosen default complexity boundary. | Proposed |
| FLH-F-038 | The manager agent shall attempt a first CAD iteration by default. | The manager should bias toward progress rather than unnecessary clarification. | Proposed |
| FLH-F-039 | The manager agent shall ask clarifying questions before first-pass CAD generation only when critical gaps make a credible initial model impossible. | Clarification should block only when it materially prevents a believable first iteration. | Proposed |
| FLH-F-040 | For the purpose of first-pass generation, critical gaps shall include missing information about core function, mandatory interfaces, must-hit dimensions or tolerances, or other blocking constraints. | The clarification threshold must be explicit enough to implement and test. | Proposed |
| FLH-F-041 | When the manager agent proceeds without clarification, it shall record explicit assumptions in structured run state. | Assumption traceability is required when the system moves forward under ambiguity. | Proposed |
| FLH-F-042 | The CAD Designer shall operate with the persona and decision quality expected of a Mechanical Design Engineer, prioritizing standards-aware, manufacturable, and spec-grounded modeling. | The CAD Designer is expected to behave like an engineering specialist rather than a generic code generator. | Proposed |
| FLH-F-043 | The CAD Designer may invoke the Design Researcher ad hoc when external factual knowledge would materially improve the design, especially for named parts, mechanisms, conventions, or standards such as fasteners, gears, and escapements. | Named engineering terms often imply external standards and conventions that should inform the design. | Proposed |
| FLH-F-044 | The operator CLI shall support profile-aware execution for `formloop run`, `formloop eval run`, and `formloop doctor`. | Named profiles must be usable through the primary operator surfaces. | Proposed |
| FLH-F-045 | `formloop doctor` shall validate required keys, the selected profile, provider/model resolvability, and missing dependency or configuration issues before first run. | Early validation reduces avoidable failures during development and normal use. | Proposed |
| FLH-F-046 | The harness shall capture the effective run profile, provider, model, and thinking level in per-run and per-revision metadata. | Effective runtime configuration is a core part of traceability and debugging. | Proposed |
| FLH-F-047 | The harness shall record structured clarification events and structured assumption records in run state. | Clarification behavior and assumption-taking must be inspectable after the fact. | Proposed |

### Non-functional requirements

| ID         | Requirement                                                                                                                      | Rationale                                                                                   | Status   |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | -------- |
| FLH-NF-001 | The harness shall enable maximal autonomy while maintaining safety and reliability.                                                  | Safety and reliability are explicit project objectives.                                     | Proposed |
| FLH-NF-002 | The harness shall emit intermediate progress updates during multi-step runs in a form suitable for streaming consumption.        | Progress visibility is required by the UI and by operator tooling.                          | Proposed |
| FLH-NF-003 | The harness shall preserve artifact traceability across runs, revisions, review steps, and eval results.                         | Traceability is a cross-cutting design objective.                                           | Proposed |
| FLH-NF-004 | The harness shall support reproducible eval execution for regression tracking.                                                   | Developer evals must be usable as a stable quality bar over time.                           | Proposed |
| FLH-NF-005 | The harness shall be operable in a headless environment through its CLI and CI integrations even if the UI is not running.      | Automation and CI must not depend on an interactive UI session.                             | Proposed |
| FLH-NF-006 | The harness shall keep the internal design loop and developer eval loop conceptually distinct in both implementation and reporting. | The user explicitly requested clarity between these two modes.                              | Proposed |
| FLH-NF-007 | The harness shall expose enough logs and structured data to debug failures in design runs and eval runs.                         | High-quality iteration depends on diagnosability.                                           | Proposed |
| FLH-NF-008 | The harness should minimize unnecessary context growth by using specialist boundaries and skills intentionally.                  | Context cleanliness is one of the explicit reasons for the subagent and skill architecture. | Proposed |
| FLH-NF-009 | The harness shall support CI reporting on push to main and a smaller smoke path for PRs.                                         | This is part of the agreed developer workflow.                                              | Proposed |
| FLH-NF-010 | The harness shall provide provider-agnostic run tracing and observability across supported model providers.                      | Traceability must remain available even when multiple providers are supported.              | Proposed |
| FLH-NF-011 | The harness shall target near-full parity for core harness flows across OpenAI and Anthropic-backed runs, while not promising identical provider-specific behavior for every advanced feature. | The user wants strong cross-provider support without overpromising adapter-dependent behavior. | Proposed |

### Design and technical constraint requirements

| ID        | Requirement                                                                                                                                | Rationale                                                                                          | Status   |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- | -------- |
| FLH-D-001 | The harness shall use `cad-cli` as its deterministic CAD tool substrate rather than embedding those responsibilities directly.             | The architecture deliberately separates deterministic tool execution from the application harness. | Proposed |
| FLH-D-002 | The harness shall use build123d as the primary modeling backend exposed through its design workflows.                                      | This is a core technical decision for the project.                                                 | Proposed |
| FLH-D-003 | The harness shall produce Blender-rendered GLB outputs as the standard geometry artifact delivered to downstream consumers.                | GLB is the agreed interchange format for both UI viewing and agent-facing rendered review.         | Proposed |
| FLH-D-004 | The harness shall treat STEP as the authoritative geometry artifact in its internal state and eval workflows.                              | STEP is the agreed source-of-truth artifact for CAD and comparison.                                | Proposed |
| FLH-D-005 | The harness shall expose a centralized internal runtime abstraction for CLI execution, Python execution, artifact reads, and artifact writes. | The agreed harness uses a constrained runtime rather than a broker service.                     | Proposed |
| FLH-D-006 | The harness shall not require a separate tool broker service in v1.                                                                        | The user explicitly rejected a broker-based design for the initial architecture.                   | Proposed |
| FLH-D-007 | The harness shall represent the current design state explicitly rather than reconstructing it from raw chat alone.                         | The UI and manager both depend on a normalized current state object.                               | Proposed |
| FLH-D-008 | The harness shall keep internal review artifacts and eval artifacts distinct, even when some underlying tools are shared.                  | The project requires clarity between internal review and developer evaluation.                     | Proposed |
| FLH-D-009 | The harness shall support standardized output schemas for deterministic metrics and judge outputs.                                         | Evals require consistent aggregation and CI reporting.                                             | Proposed |
| FLH-D-010 | The harness shall reserve an optional future integration point for printability validation but shall not make it a core release requirement. | 3D printing validation is intentionally deferred from the core project boundary.                 | Proposed |
| FLH-D-011 | The harness shall maintain a checked-in, non-secret configuration file for named run profiles and runtime defaults. | The chosen configuration model separates shareable defaults from secrets. | Proposed |
| FLH-D-012 | Secrets shall be supplied through environment variables only and shall not be committed to the repository. | This keeps secret handling simple and safe for both development and normal execution. | Proposed |
| FLH-D-013 | Environment variable support shall include at minimum `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` when the corresponding providers are enabled. | The initial provider set requires explicit key contracts. | Proposed |
| FLH-D-014 | The harness shall normalize provider-specific thinking controls behind a shared configuration abstraction rather than exposing provider-specific reasoning parameters directly in the primary config surface. | A small cross-provider control surface is easier to use and maintain. | Proposed |

### Validation and UAT requirements

| ID        | Requirement | Rationale | Status   |
| --------- | ----------- | --------- | -------- |
| FLH-V-001 | The harness shall maintain strong unit-test coverage over deterministic logic, schema and config parsing, and run-state serialization behavior. | Deterministic logic and contracts should be validated at the smallest practical scope. | Proposed |
| FLH-V-002 | The harness shall maintain integration coverage for agent orchestration, runtime and tool boundaries, persistence, and artifact and report generation. | Cross-boundary behavior is central to the product and cannot be proven by unit tests alone. | Proposed |
| FLH-V-003 | The harness shall run critical smoke tests for end-to-end operator flows on pull requests. | PR validation should quickly catch major regressions in the most important flows. | Proposed |
| FLH-V-004 | The harness shall run broader eval and user-acceptance coverage on `main` and before release readiness decisions. | Release confidence requires broader evidence than the PR smoke path. | Proposed |
| FLH-V-005 | The harness requirements shall maintain an explicit catalog of critical user and operator UAT scenarios with acceptance criteria. | Important flows should be defined up front so implementation and validation stay aligned. | Proposed |
| FLH-V-006 | Acceptance criteria for critical flows shall require system-boundary evidence such as surfaced clarification behavior, profile selection, artifact generation, review outputs, and recorded run metadata. | The project definition of done requires evidence from the real workflow boundary. | Proposed |

### Configuration and runtime contract

The harness configuration baseline is intentionally small:

- The checked-in non-secret configuration file shall live at the repo root as `formloop.harness.toml`.
- The initial named profiles are `normal`, `dev_test`, and `eval`.
- Local development secrets should be loaded from a repo-root `.env.local` file into environment variables at process start; `.env.local` shall remain untracked.
- CI and regular deployed execution shall provide the same secrets through environment variables rather than a checked-in file.
- The minimum environment variable contract is `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`, with provider-specific keys only required when the corresponding provider is enabled.

The initial profile defaults are:

| Profile | Default provider path | Default model | Default thinking | Purpose |
| ------- | --------------------- | ------------- | ---------------- | ------- |
| `normal` | OpenAI Responses | `gpt-5.4` | `high` | Normal user-facing execution where design quality matters most. |
| `dev_test` | OpenAI Responses | `gpt-5.4-nano` | `low` | Cheap developer plumbing checks and smoke validation. |
| `eval` | OpenAI Responses | `gpt-5.4` | `high` | Higher-fidelity eval and benchmarking runs unless an alternate provider is intentionally under test. |

The stable run-state contract shall include:

- effective profile
- effective provider path
- effective model
- effective thinking level
- structured clarification events
- structured recorded assumptions

### UAT scenarios and acceptance criteria

The following user and operator flows are mandatory UAT coverage for the harness:

| ID | Scenario | Acceptance criteria | Required evidence |
| -- | -------- | ------------------- | ----------------- |
| UAT-001 | Fully specified new design request | A first candidate is generated without clarification and the run surfaces artifacts plus a review summary. | Run record, generated artifacts, review summary, effective profile metadata. |
| UAT-002 | Critically underspecified request | The manager blocks first-pass CAD generation long enough to ask for the missing information. | Surfaced clarification event, blocked generation state, clarification prompt contents. |
| UAT-003 | Partially ambiguous request | The manager proceeds with a first pass and records explicit assumptions instead of blocking. | Generated candidate, structured assumptions, review summary, effective profile metadata. |
| UAT-004 | Standards-backed request | The system invokes or records relevant external research before or during modeling when named standards, mechanisms, or commodity parts are implicated. | Research trace, cited factual findings, updated spec or modeling inputs. |
| UAT-005 | Reference-image-assisted request | The internal review loop consumes the reference image alongside rendered model outputs. | Reference image attachment, review trace, review summary with image-informed findings. |
| UAT-006 | Revision after internal review | The Review Specialist requests revision feedback and a later iteration is generated. | Review finding requesting revision, subsequent revision artifacts, updated review summary. |
| UAT-007 | Profile-aware run execution | `formloop run` succeeds with both the `normal` profile and an alternate Anthropic-backed profile. | CLI invocation record, effective profile/provider/model metadata, successful run outputs. |
| UAT-008 | Eval execution | `formloop eval run` produces deterministic metrics, judge outputs, and aggregate reporting artifacts. | Per-case outputs, aggregate summary, judge outputs JSON, deterministic metrics JSON. |
| UAT-009 | Doctor validation | `formloop doctor` fails cleanly when required keys are missing and passes when configuration is valid. | CLI output for failure and success cases, validation details for keys and profiles. |
| UAT-010 | End-to-end traceability | Traceability is preserved across run input, spec, research, artifacts, review, and final output. | Inspectable run record tying together spec state, research, artifacts, review results, and effective runtime metadata. |

### Development auth setup

Before implementation work begins, local development should be initialized as follows:

1. Create `/Users/jdegregorio/Repos/formloop/.env.local`.
2. Set at minimum:
   - `OPENAI_API_KEY=...`
   - `ANTHROPIC_API_KEY=...`
3. Keep provider/model profile selection in `formloop.harness.toml`, not in `.env.local`.
4. Use `.env.example` as the tracked template for required secret names only.

These requirements are meant to be a working baseline. The most important maintenance rule is simple: **keep the Status column current as development progresses**, so the spec remains a living control document rather than a one-time design artifact.
