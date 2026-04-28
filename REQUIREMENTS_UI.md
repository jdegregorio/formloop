## Requirements Specification for Formloop - UI

**Scope**: This document covers the Formloop user-facing web UI, which is a mostly independent build that integrates with the harness through its HTTP programmatic interface. Harness, agent, CLI, and eval requirements are tracked separately in [REQUIREMENTS_HARNESS.md](REQUIREMENTS_HARNESS.md).

**Important**: Keep each requirement status up to date during development. Include comments that reference requirements in-code wherever possible.

### Functional requirements

| ID | Requirement | Rationale | Status |
| -- | ----------- | --------- | ------ |
| FLU-F-001 | The UI shall provide a chat-based interface for submitting design requests and revisions. | Chat is the primary human interaction surface. | Proposed |
| FLU-F-002 | The UI shall display the normalized current fit/form/function specification for the active design, as provided by the harness. | The current spec is a core user-facing object in the agreed design. | Proposed |
| FLU-F-003 | The UI shall provide an interactive GLB viewer through which the user can orbit, pan, and zoom the latest candidate geometry. | Interactive viewing is more useful for a human user than a fixed multi-view render sheet. | Proposed |
| FLU-F-004 | The UI's GLB viewer shall be implemented using a browser-native WebGL stack, with Three.js via `GLTFLoader` as the recommended default and `<model-viewer>` as an acceptable lighter-weight alternative if advanced inspection features are not yet needed. | Browser-native viewing gives the human user full control over camera state while keeping the UI responsive. | Proposed |
| FLU-F-005 | The UI shall treat the interactive GLB viewer as the only required user-facing geometry review surface. Harness render sheet and per-view images may be exposed through secondary operator/debug affordances or artifact downloads, but are not required as visible panes in the default user workspace. | The product should optimize for human-friendly interactive model exploration while preserving access to persisted artifacts when needed. | Proposed |
| FLU-F-006 | The UI shall expose a concise top-level design understanding summary that combines the latest normalized spec snapshot and latest review summary. | The UI should show what the harness understood and how the latest candidate evaluated without overwhelming detail. | Proposed |
| FLU-F-007 | The UI shall expose downloadable artifacts including STEP, GLB, render sheet, and model source when available. | Artifact download is part of the core user flow. | Proposed |
| FLU-F-008 | The UI shall provide expandable access to run trace history (including tool-call summaries, orchestration events, and intermediate traces), collapsed by default. | Traceability is required, but secondary details should stay out of the primary UI by default. | Proposed |
| FLU-F-009 | The UI shall surface intermediate progress updates by polling the harness for the current run snapshot plus append-only events, and shall render `latest_narration` from snapshots as the primary live status line while still preserving structured milestone breadcrumbs for expandable trace/history views. | The agreed v1 interface is polling-based and should explain what the harness is doing and why in both concise and machine-readable forms. | Proposed |
| FLU-F-010 | The UI shall allow the user to attach one optional reference image per request for use in the harness's closed-loop review. | Reference-image review remains a first-class capability. | Proposed |
| FLU-F-011 | The UI shall consume the harness's programmatic interface rather than re-implementing harness logic client-side. | The UI is a separate build and must integrate through a clean contract. | Proposed |
| FLU-F-012 | The UI shall present one continuous design-thread session even when multiple runs exist underneath it. | The user should perceive one coherent design experience rather than disconnected executions. | Proposed |
| FLU-F-013 | The UI shall keep revisions visible across the full session history, including revisions from earlier runs in the same session. | Reviewing prior iterations is part of traceability and design continuity. | Proposed |
| FLU-F-014 | The UI shall default to a three-pane workspace: left half chat thread and composer, top-right concise spec plus latest review summary, and bottom-right interactive GLB viewer. | The default layout should prioritize conversational control, concise understanding, and direct geometry inspection in one screen. | Proposed |

### Non-functional requirements

| ID | Requirement | Rationale | Status |
| -- | ----------- | --------- | ------ |
| FLU-NF-001 | The UI shall prioritize intuitive, low-noise presentation by default. | The agreed UI philosophy emphasizes clarity and avoids exposing excess detail. | Proposed |
| FLU-NF-002 | The UI shall remain responsive while the harness is executing long-running operations. | Interactivity cannot depend on harness work completing. | Proposed |
| FLU-NF-003 | The UI shall degrade gracefully when partial run state is available, such as spec present but no geometry yet. | Multi-step runs emit state progressively; the UI must not assume all artifacts exist at once. | Proposed |
| FLU-NF-004 | The UI shall not be a hard dependency of automation or CI flows. | Automation and CI must continue to work through the harness CLI even when the UI is down. | Proposed |
| FLU-NF-005 | The UI's GLB viewer shall support the geometry sizes expected from typical build123d outputs without prohibitive load times. | Interactive viewing is only useful if it stays usable for real project scales. | Proposed |

### Design and technical constraint requirements

| ID | Requirement | Rationale | Status |
| -- | ----------- | --------- | ------ |
| FLU-D-001 | The UI shall be built as a browser-delivered web application and shall not require a desktop client in v1. | Browser delivery matches the agreed product posture. | Proposed |
| FLU-D-002 | The UI shall treat GLB as its primary geometry-viewing artifact and shall not attempt exact CAD-accurate measurement in-browser. | GLB is a presentation artifact; exact CAD interrogation belongs on the harness side against STEP. | Proposed |
| FLU-D-003 | Any CAD-accurate measurement, sectioning, or feature interrogation shown in the UI shall be computed on the harness side and delivered as structured data. | This keeps the browser viewer focused on presentation and the harness as the source of truth. | Proposed |
| FLU-D-004 | The UI shall communicate with the harness through its stable HTTP programmatic interface only, and shall not read harness internal state directly. | Clean contract boundaries let the UI evolve independently. | Proposed |
| FLU-D-005 | The UI shall present normal design review outputs and developer eval outputs distinctly when both surfaces are exposed. | The two review contexts should remain understandable to the user even if they share underlying specialist logic. | Proposed |
| FLU-D-006 | The UI shall treat the interactive GLB viewer as the primary geometry surface in the default workspace. Render sheet and per-view images, when exposed, shall be treated as optional non-primary artifact surfaces. | This removes ambiguity about the intended primary preview experience and keeps artifact-heavy views secondary. | Proposed |
| FLU-D-007 | The UI shall rely on polling rather than transport streaming for run progress in v1. | The harness contract is HTTP-only with async polling semantics. | Proposed |
| FLU-D-008 | The UI shall constrain v1 reference-image upload support to one optional PNG or JPEG per request. | This keeps the initial UI and API contracts intentionally small and aligned. | Proposed |
| FLU-D-009 | The UI shall use harness event semantics (phase-tagged narration plus structured milestones) rather than hard-coding internal agent identities in user-facing trace labels. | Harness internals may evolve (for example direct research calls vs specialist agents), but the UI contract should stay stable and understandable. | Proposed |

These requirements are meant to be a working baseline. The most important maintenance rule is simple: **keep the Status column current as development progresses**, so the spec remains a living control document rather than a one-time design artifact.
