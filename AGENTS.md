# AGENTS.md

Instructions for coding agents working in Formloop.

Formloop is the main application for an agentic CAD system. It turns user intent into geometry through constrained tool use, revision loops, preview rendering, and eval-driven quality measurement. Your job is not just to make it run. Your job is to make it provably work.

## Mission

Build an application that can:

- accept natural language design requirements
- manage iterative CAD generation and revision loops
- present specs, previews, and artifacts clearly to users
- maintain strong traceability across runs and revisions
- evaluate quality with repeatable developer datasets and scoring

## Prime directive

**Closed-loop validation and feedback loops are mandatory.**

Do not treat agent output, rendered previews, or passing unit tests as sufficient proof by themselves. The system is only working when the right evidence closes the loop between user intent, generated artifacts, validation results, and surfaced feedback.

## Core operating rules

1. **Evidence beats confidence**
   - Never claim a feature works without validation evidence.
   - Prefer measured results, captured artifacts, and regression checks over narrative summaries.

2. **The loop matters as much as the generation**
   - Formloop is not just a one-shot CAD generator.
   - Preserve the review, critique, revision, and reevaluation cycle as a first-class product behavior.

3. **Keep app logic and deterministic CAD logic separate**
   - Geometry build/render/compare primitives belong in `cad-cli`.
   - Formloop should orchestrate them, not quietly duplicate them.

4. **Traceability is a product feature**
   - Maintain clear links between prompt/spec, intermediate state, generated artifacts, validation outcomes, and final outputs.
   - A good run should be inspectable after the fact.

5. **Optimize for maintainability over demo magic**
   - Avoid hidden prompts, ad hoc glue, or fragile state that only works in one golden path.

## Definition of done

A task is not done unless the relevant loop is closed.

That typically means:

- implementation is complete
- automated tests are added or updated
- the changed user or operator flow is exercised
- artifacts are generated and inspected where relevant
- review/feedback signals are surfaced correctly
- failure cases are handled and demonstrated where practical
- docs or operator-facing guidance are updated when behavior changes
- billing or cost implications are noted when model/tool usage changes materially

If you cannot prove part of the loop, say so explicitly.

## Required validation mindset

Validation should follow the system boundary, not just the edited function.

### For UI or API changes

Validate:

- the request path or interaction path
- the resulting state transition
- the surfaced response or UI summary
- the linked artifact references or review outputs

### For agent orchestration changes

Validate:

- routing behavior
- context assembly
- specialist handoff expectations
- internal review outputs
- retry/revision logic where relevant
- persistence of run state and artifacts

### For artifact pipeline changes

Validate:

- correct invocation of `cad-cli`
- expected artifact creation
- traceability metadata
- preview availability
- correct propagation of authoritative versus presentation artifacts

### For eval harness changes

Validate:

- dataset loading
- run execution against known-truth cases
- scoring logic
- diagnostic output
- regression detection and reporting

### For prompt or policy changes

Do not stop at “it sounds better.” Validate:

- representative task outcomes
- failure/recovery behavior
- review loop quality
- any measurable effect on eval results if possible

## Closed-loop development workflow

For non-trivial changes, follow this cycle:

1. define the intended user-visible or system-visible outcome
2. identify the evidence needed to prove it
3. implement the smallest useful slice
4. run targeted tests
5. exercise the real flow end-to-end or at least across the relevant boundary
6. inspect state, artifacts, and surfaced outputs
7. fix what the evidence says is broken
8. repeat until the claim is supported

A completed loop should answer:

- what changed?
- what evidence proves it?
- what remains unproven?

## Testing expectations

- prefer fast targeted tests during iteration
- add integration tests for cross-boundary behavior
- add end-to-end tests for critical happy paths
- create regression tests for discovered bugs
- use fixture datasets for eval-related behavior where practical
- ensure tests assert meaningful outputs, not just status codes

## Eval-first expectations

Formloop should grow with a repeatable eval culture.

When building features that affect output quality:

- ask how this will be measured
- add or update eval cases when practical
- capture representative failures, not just successes
- prefer comparable before/after evidence over anecdotal wins

If a feature cannot yet be measured systematically, note the gap and suggest the smallest credible eval to add next.

## Billing and cost discipline

This system may incur cost through model calls, rendering, and repeated tool execution.

When modifying behavior that changes cost profile:

- note which calls or jobs increase in frequency or size
- avoid wasteful loops or duplicate expensive work
- use targeted tests before full end-to-end runs
- surface cost-sensitive paths clearly in code and docs
- do not silently multiply inference or rendering passes

## Implementation preferences

- keep state models explicit
- make artifact identifiers and paths stable
- prefer append-only run records over mutable mystery state
- make review findings structured where possible
- design operator/debug outputs for real diagnosis, not theater
- keep prompts/resources organized and versionable
- favor constrained interfaces between agents and tools

## Safety and permission boundaries

Ask before:

- adding new paid external services or major dependencies
- changing public artifact contracts significantly
- introducing destructive cleanup behavior
- adding background loops, daemons, or autonomous behavior not already intended
- weakening validation in the name of speed

## Repo-specific architectural reminders

- Formloop is the main application, not the deterministic CAD toolkit
- `cad-cli` is the portable deterministic CAD layer and owns the `cad` command surface
- `build123d` is the primary modeling backend
- Blender is the standard renderer
- STEP is authoritative
- GLB is the presentation artifact
- geometry comparison is first-class
- alignment and comparison should remain conceptually separate
- keep the runtime abstraction small: run CLI commands, run constrained Python, read artifacts, write artifacts
- the v1 harness should be multi-agent but intentionally small and controlled
- the manager maintains the active fit, form, and function spec and routes work, but should not do heavy CAD authoring directly
- preserve the distinction between the internal Review Specialist loop and the Eval Specialist benchmarking/CI role

## Skill expectations

Skills are reusable capability guides, not tiny macros.

When creating or updating skills for this repo, include:

- purpose and scope
- which agent uses the skill
- relevant tools and commands
- common workflows
- conventions
- common failures and recovery patterns
- expected artifacts

Suggested v1 skill areas:

- `build123d_modeling`
- `cad_artifact_conventions`
- `blender_rendering`
- `geometry_comparison`
- `design_research`
- `internal_design_review`
- `eval_execution`
- `reference_image_review`

## Good agent behavior

- keep diffs focused
- document assumptions and contract changes
- leave behind testable systems, not fragile demos
- summarize validation evidence clearly
- flag uncertainty instead of bluffing
- preserve architectural boundaries
- keep the UI oriented toward design review rather than raw trace output by default

## Bad agent behavior

- shipping based on vibes
- conflating pretty renders with correct geometry
- bypassing evals or review loops because the demo looked fine
- duplicating `cad-cli` logic inside the app
- reporting completion without proof
