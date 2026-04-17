## Requirements specification for Formloop - UI

**Scope**: This document covers requirements for the Formloop user-facing web UI, which is a mostly independent build that integrates with the agent harness through its HTTP programmatic interface. Harness, agent, CLI, and eval requirements are tracked separately in [REQUIREMENTS_HARNESS.md](REQUIREMENTS_HARNESS.md).

**Important**: Keep each requirement status up to date during development. Include comments that reference requirements in-code wherever possible.

### Functional requirements

| ID        | Requirement | Rationale | Status   |
| --------- | ----------- | --------- | -------- |
| FLU-F-001 | The UI shall provide a chat-based interface for submitting design requests and revisions. | Chat is the primary human interaction surface. | Proposed |
| FLU-F-002 | The UI shall display the normalized current fit/form/function specification for the active design, as provided by the harness. | The current spec is a core user-facing object in the agreed design. | Proposed |
| FLU-F-003 | The UI shall provide an interactive GLB viewer through which the user can orbit, pan, and zoom the latest candidate geometry. | Interactive viewing is more useful for a human user than a fixed multi-view render sheet. | Proposed |
| FLU-F-004 | The UI's GLB viewer shall be implemented using a browser-native WebGL stack, with Three.js via `GLTFLoader` as the recommended default and `<model-viewer>` as an acceptable lighter-weight alternative if advanced inspection features are not yet needed. | Browser-native viewing gives the human user full control over camera state while keeping the UI responsive. | Proposed |
| FLU-F-005 | The UI shall make the harness-produced rendered images, including the multi-view render sheet and individual persisted view images, available to the user as a secondary reference alongside the interactive GLB viewer. | Rendered images remain a useful reference, especially for comparing against the closed-loop review signal. | Proposed |
| FLU-F-006 | The UI shall expose a concise latest review summary to the user. | The UI should show the state of the internal review loop without overwhelming detail. | Proposed |
| FLU-F-007 | The UI shall expose downloadable artifacts including STEP, GLB, render sheet, and model source when available. | Artifact download is part of the core user flow. | Proposed |
| FLU-F-008 | The UI shall provide expandable access to tool-call history, subagent-call history, and intermediate traces, collapsed by default. | Traceability is required, but secondary details should stay out of the primary UI by default. | Proposed |
| FLU-F-009 | The UI shall surface intermediate progress updates by polling the harness for a current run snapshot plus append-only structured events. | The agreed v1 interface is polling-based rather than streaming-based. | Proposed |
| FLU-F-010 | The UI shall allow the user to attach one optional reference image per request for use in the harness's closed-loop review. | Reference-image review is a first-class review capability and must be reachable from the UI. | Proposed |
| FLU-F-011 | The UI shall consume the harness's programmatic interface rather than re-implementing harness logic client-side. | The UI is a separate build and must integrate with the harness through a clean contract. | Proposed |
| FLU-F-012 | The UI shall present one continuous design-thread session even when multiple runs exist underneath it. | The user should perceive one coherent design experience rather than disconnected executions. | Proposed |
| FLU-F-013 | The UI shall keep revisions visible across the full session history, including revisions from earlier runs in the same session. | Reviewing prior iterations is part of traceability and design continuity. | Proposed |

### Non-functional requirements

| ID         | Requirement | Rationale | Status   |
| ---------- | ----------- | --------- | -------- |
| FLU-NF-001 | The UI shall prioritize intuitive, low-noise presentation by default. | The agreed UI philosophy emphasizes clarity and avoids exposing excess detail. | Proposed |
| FLU-NF-002 | The UI shall remain responsive while the harness is executing long-running operations. | Interactivity cannot depend on harness work completing. | Proposed |
| FLU-NF-003 | The UI shall degrade gracefully when partial run state is available, such as spec present but no geometry yet. | Multi-step runs emit state progressively; the UI must not assume all artifacts exist at once. | Proposed |
| FLU-NF-004 | The UI shall not be a hard dependency of automation or CI flows. | Automation and CI must continue to work through the harness CLI even when the UI is down. | Proposed |
| FLU-NF-005 | The UI's GLB viewer shall support the geometry sizes expected from typical build123d outputs without prohibitive load times. | Interactive viewing is only useful if it stays usable for real project scales. | Proposed |

### Design and technical constraint requirements

| ID        | Requirement | Rationale | Status   |
| --------- | ----------- | --------- | -------- |
| FLU-D-001 | The UI shall be built as a browser-delivered web application and shall not require a desktop client in v1. | Browser delivery matches the agreed product posture. | Proposed |
| FLU-D-002 | The UI shall treat GLB as its primary geometry-viewing artifact and shall not attempt exact CAD-accurate measurement in-browser. | GLB is a mesh or scene format; exact CAD interrogation belongs on the harness side against STEP. | Proposed |
| FLU-D-003 | Any CAD-accurate measurement, sectioning, or feature interrogation shown in the UI shall be computed on the harness side and delivered as structured data. | This keeps the browser viewer focused on presentation and the harness as the source of truth. | Proposed |
| FLU-D-004 | The UI shall communicate with the harness through its stable HTTP programmatic interface only, and shall not read harness internal state directly. | Clean contract boundaries let the UI evolve as an independent build. | Proposed |
| FLU-D-005 | The UI shall present internal design-loop review and developer eval review distinctly when both surfaces are exposed. | The project requires clarity between these two modes in both implementation and reporting. | Proposed |
| FLU-D-006 | The UI shall treat the interactive GLB viewer as the primary geometry surface and the render sheet as a secondary artifact-driven reference surface. | This removes ambiguity about the intended primary preview experience. | Proposed |
| FLU-D-007 | The UI shall rely on polling rather than transport streaming for run progress in v1. | The harness contract is HTTP-only with async polling semantics. | Proposed |
| FLU-D-008 | The UI shall constrain v1 reference-image upload support to one optional PNG or JPEG per request. | This keeps the initial UI and API contracts intentionally small and aligned. | Proposed |

These requirements are meant to be a working baseline. The most important maintenance rule is simple: **keep the Status column current as development progresses**, so the spec remains a living control document rather than a one-time design artifact.
