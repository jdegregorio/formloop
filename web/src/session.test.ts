import { describe, expect, it } from "vitest";

import {
  artifactRolesFromSnapshot,
  buildSubmittedPrompt,
  createEmptySession,
  loadSession,
  mergeEvents,
  saveSession,
  userFacingArtifactRoles
} from "./session";
import type { RunSnapshot } from "./types";

function snapshot(partial: Partial<RunSnapshot> = {}): RunSnapshot {
  return {
    schema_version: 1,
    run_id: "uuid",
    run_name: "run-0001",
    status: "running",
    input_summary: "cube",
    status_detail: null,
    generated_at: "2026-01-01T00:00:00Z",
    current_spec: { form: "cube" },
    current_revision_name: "rev-001",
    delivered_revision_name: null,
    revisions: ["rev-001"],
    assumptions: [],
    research_findings: [],
    effective_role_runtimes: {},
    final_answer: null,
    latest_review_decision: null,
    latest_review_summary_path: "revisions/rev-001/review-summary.json",
    artifacts: {
      schema_version: 1,
      step_path: "/runs/run-0001/revisions/rev-001/model.step",
      glb_path: "/runs/run-0001/revisions/rev-001/model.glb",
      render_sheet_path: "/runs/run-0001/revisions/rev-001/render-sheet.png",
      view_paths: ["/runs/run-0001/revisions/rev-001/views/front.png"]
    },
    last_event_index: 0,
    last_event_kind: null,
    last_message: null,
    latest_narration: null,
    latest_narration_index: null,
    latest_narration_phase: null,
    ...partial
  };
}

describe("session persistence", () => {
  it("round trips the browser session", () => {
    const store = new Map<string, string>();
    const storage = {
      getItem: (key: string) => store.get(key) || null,
      setItem: (key: string, value: string) => store.set(key, value)
    };
    const session = {
      ...createEmptySession(),
      activeRunName: "run-0001"
    } as const;

    saveSession(session, storage);

    expect(loadSession(storage).activeRunName).toBe("run-0001");
  });

  it("merges event pages by index", () => {
    const events = mergeEvents(
      [
        {
          schema_version: 1,
          index: 1,
          kind: "narration",
          ts: "",
          message: "old",
          phase: "plan",
          narration_error: null,
          data: {}
        }
      ],
      [
        {
          schema_version: 1,
          index: 1,
          kind: "narration",
          ts: "",
          message: "new",
          phase: "review",
          narration_error: null,
          data: {}
        },
        {
          schema_version: 1,
          index: 2,
          kind: "delivered",
          ts: "",
          message: "done",
          phase: null,
          narration_error: null,
          data: {}
        }
      ]
    );

    expect(events.map((event) => event.message)).toEqual(["new", "done"]);
  });

  it("builds follow-up prompts with visible current context", () => {
    const prompt = buildSubmittedPrompt(
      "make it taller",
      snapshot({ current_spec: { height_mm: 20 } }),
      {
        schema_version: 2,
        decision: "revise",
        outcome: "revise",
        summary: "The model is too short.",
        next_step: "Increase the height.",
        key_findings: ["too short"],
        revision_instructions: "increase height"
      }
    );

    expect(prompt).toContain("make it taller");
    expect(prompt).toContain("height_mm");
    expect(prompt).toContain("too short");
  });

  it("derives artifact roles from snapshots", () => {
    expect(artifactRolesFromSnapshot(snapshot())).toEqual(
      expect.arrayContaining(["step", "glb", "render_sheet", "view_front", "review"])
    );
  });

  it("filters internal manifest roles from the user-facing artifact list", () => {
    expect(
      userFacingArtifactRoles(snapshot(), ["build_metadata", "inspect_summary", "view_top"])
    ).toEqual(
      expect.arrayContaining([
        "step",
        "glb",
        "render_sheet",
        "model_py",
        "manifest",
        "review",
        "view_front",
        "view_top"
      ])
    );
    expect(
      userFacingArtifactRoles(snapshot(), ["build_metadata", "inspect_summary"])
    ).not.toContain("build_metadata");
  });
});
