import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ChatPane } from "./ChatPane";
import { ArtifactMenu } from "./ArtifactMenu";
import { SummaryPane } from "./SummaryPane";
import { ViewerPane } from "./ViewerPane";
import { RevisionTimeline } from "./RevisionTimeline";
import type { DesignThreadSessionV1, RunSnapshot } from "../types";

const snapshot: RunSnapshot = {
  schema_version: 1,
  run_id: "uuid",
  run_name: "run-0001",
  status: "running",
  input_summary: "cube",
  status_detail: null,
  generated_at: "2026-01-01T00:00:00Z",
  current_spec: {
    name: "Mounting plate",
    design_intent: "Hold a sensor",
    features: ["two centered holes", "flat rectangular body"],
    constraints: ["hidden in concise UI"]
  },
  current_revision_name: "rev-001",
  delivered_revision_name: null,
  revisions: ["rev-001"],
  assumptions: [],
  research_findings: [],
  effective_role_runtimes: {},
  final_answer: null,
  latest_review_decision: "pass",
  latest_review_summary_path: "review-summary.json",
  artifacts: {
    schema_version: 1,
    step_path: "model.step",
    glb_path: "model.glb",
    render_sheet_path: "render-sheet.png",
    view_paths: []
  },
  last_event_index: 1,
  last_event_kind: "narration",
  last_message: "reviewing",
  latest_narration: "checking the hole pattern",
  latest_narration_index: 1,
  latest_narration_phase: "review"
};

describe("workspace components", () => {
  it("shows complete narration history while keeping raw trace collapsed", () => {
    const { container } = render(
      <ChatPane
        messages={[]}
        prompt=""
        attachment={null}
        submitting={false}
        error={null}
        latestNarration="checking the model"
        latestNarrationPhase="review"
        events={[
          {
            schema_version: 1,
            index: 0,
            kind: "narration",
            ts: "",
            message: "normalizing the request",
            phase: "plan",
            narration_error: null,
            data: {}
          },
          {
            schema_version: 1,
            index: 1,
            kind: "narration",
            ts: "",
            message: "checking the model",
            phase: "review",
            narration_error: null,
            data: {}
          }
        ]}
        onPromptChange={vi.fn()}
        onAttachmentChange={vi.fn()}
        onSubmit={vi.fn()}
      />
    );

    const history = container.querySelector(".narration-history");
    expect(history).toHaveAttribute("open");
    expect(history?.textContent).toContain("normalizing the request");
    expect(history?.textContent).toContain("checking the model");
    expect(screen.getByText("Trace").closest("details")).not.toHaveAttribute("open");
  });

  it("nests completed narration above the final answer", () => {
    const { container } = render(
      <ChatPane
        messages={[
          {
            id: "user-run-1",
            role: "user",
            text: "make a gear",
            createdAt: "2026-01-01T00:00:00Z",
            runName: "run-0001"
          },
          {
            id: "agent-run-1",
            role: "agent",
            text: "final response",
            createdAt: "2026-01-01T00:01:00Z",
            runName: "run-0001"
          }
        ]}
        activeRunName="run-0001"
        prompt=""
        attachment={null}
        submitting={false}
        error={null}
        latestNarration="delivering the model"
        latestNarrationPhase="final"
        events={[
          {
            schema_version: 1,
            index: 0,
            kind: "narration",
            ts: "",
            message: "planning the shape",
            phase: "plan",
            narration_error: null,
            data: {}
          },
          {
            schema_version: 1,
            index: 1,
            kind: "narration",
            ts: "",
            message: "reviewing the geometry",
            phase: "review",
            narration_error: null,
            data: {}
          }
        ]}
        onPromptChange={vi.fn()}
        onAttachmentChange={vi.fn()}
        onSubmit={vi.fn()}
      />
    );

    const agentMessage = container.querySelector(".message-agent");
    const narration = agentMessage?.querySelector(".narration-history");

    expect(narration).toBeTruthy();
    expect(narration).not.toHaveAttribute("open");
    expect(agentMessage?.textContent?.indexOf("planning the shape")).toBeLessThan(
      agentMessage?.textContent?.indexOf("final response") || 0
    );
    expect(container.querySelectorAll(".narration-item")).toHaveLength(3);
  });

  it("submits the composer", async () => {
    const submit = vi.fn();
    render(
      <ChatPane
        messages={[]}
        prompt="cube"
        attachment={null}
        submitting={false}
        error={null}
        latestNarration={null}
        latestNarrationPhase={null}
        events={[]}
        onPromptChange={vi.fn()}
        onAttachmentChange={vi.fn()}
        onSubmit={submit}
      />
    );

    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    expect(submit).toHaveBeenCalledTimes(1);
  });

  it("submits with Enter and keeps Shift+Enter for line breaks", async () => {
    const submit = vi.fn();
    const change = vi.fn();
    render(
      <ChatPane
        messages={[]}
        prompt="cube"
        attachment={null}
        submitting={false}
        error={null}
        latestNarration={null}
        latestNarrationPhase={null}
        events={[]}
        onPromptChange={change}
        onAttachmentChange={vi.fn()}
        onSubmit={submit}
      />
    );

    const input = screen.getByPlaceholderText("A 60 mm mounting plate with two countersunk holes...");
    await userEvent.click(input);
    await userEvent.keyboard("{Enter}");
    await userEvent.keyboard("{Shift>}{Enter}{/Shift}");

    expect(submit).toHaveBeenCalledTimes(1);
  });

  it("renders spec and review summaries", () => {
    const { container } = render(
      <SummaryPane
        snapshot={{
          ...snapshot,
          assumptions: [
            {
              schema_version: 1,
              topic: "mounting",
              assumption: "holes are symmetric",
              recorded_at: "2026-01-01T00:00:00Z"
            }
          ]
        }}
        review={{
          schema_version: 2,
          decision: "pass",
          outcome: "pass",
          summary: "The hole pattern matches the request with a 60.000000300000146 mm length.",
          next_step: "Deliver this design.",
          key_findings: ["holes are centered"],
          revision_instructions: ""
        }}
      />
    );

    expect(screen.getByText("Mounting plate")).toBeInTheDocument();
    expect(screen.getByText("Hold a sensor")).toBeInTheDocument();
    expect(screen.getByText("two centered holes")).toBeInTheDocument();
    expect(screen.queryByText("hidden in concise UI")).not.toBeInTheDocument();
    expect(screen.getByText("The hole pattern matches the request with a 60 mm length.")).toBeInTheDocument();
    expect(screen.getByText("Pass")).toBeInTheDocument();
    expect(screen.getByText("Running")).toBeInTheDocument();
    expect(screen.getByText("holes are centered")).toBeInTheDocument();
    expect(screen.getByText("holes are symmetric")).toBeInTheDocument();
    expect(container.querySelector(".assumptions")?.tagName).toBe("UL");
    const sections = Array.from(container.querySelectorAll(".summary-section")).map((section) =>
      section.textContent?.trim()
    );
    expect(sections[1]).toContain("Assumptions");
    expect(sections[2]).toContain("Latest review");
  });

  it("renders compact review decision states without a chart", () => {
    const { rerender, container } = render(
      <SummaryPane
        snapshot={snapshot}
        review={{
          schema_version: 2,
          decision: "revise",
          outcome: "revise",
          summary: "The holes are misplaced.",
          next_step: "Revise the hole pattern.",
          key_findings: ["spacing is off"],
          revision_instructions: "Move the holes outward."
        }}
      />
    );

    expect(container.querySelector(".review-decision-revise")).toBeTruthy();
    expect(screen.getByText("Revise")).toBeInTheDocument();
    expect(container.querySelector(".review-outcome")).toBeNull();

    rerender(
      <SummaryPane
        snapshot={snapshot}
        review={{
          schema_version: 2,
          decision: "pass",
          outcome: "watch",
          summary: "The geometry is acceptable with one caveat.",
          next_step: "Note the caveat before delivery.",
          key_findings: ["verify material later"],
          revision_instructions: ""
        }}
      />
    );

    expect(container.querySelector(".review-watch")).toBeTruthy();
    expect(screen.getByText("Watch")).toBeInTheDocument();
    expect(screen.getByText("Evidence")).toBeInTheDocument();
  });

  it("shows an empty assumption state above latest review", () => {
    render(
      <SummaryPane
        snapshot={snapshot}
        review={{
          schema_version: 2,
          decision: "pass",
          outcome: "pass",
          summary: "The hole pattern matches the request.",
          next_step: "Deliver this design.",
          key_findings: ["holes are centered"],
          revision_instructions: ""
        }}
      />
    );

    expect(screen.getByText("No assumptions recorded.")).toBeInTheDocument();
    expect(screen.getByText("holes are centered")).toBeInTheDocument();
  });

  it("renders viewer empty state and revision selection", () => {
    const session: DesignThreadSessionV1 = {
      schemaVersion: 1,
      updatedAt: "2026-01-01T00:00:00Z",
      activeRunName: "run-0001",
      selectedRevision: null,
      messages: [],
      runs: [
        {
          runName: "run-0001",
          runId: "uuid",
          prompt: "cube",
          submittedPrompt: "cube",
          createdAt: "2026-01-01T00:00:00Z",
          statusUrl: "",
          eventsUrl: "",
          eventCursor: 0,
          snapshot: { ...snapshot, current_revision_name: null, revisions: [] },
          events: [],
          reviewSummary: null,
          artifactRoles: []
        }
      ]
    };

    render(
      <ViewerPane
        session={session}
        selected={null}
        selectedRun={session.runs[0]}
        onSelectRevision={vi.fn()}
      />
    );

    expect(screen.getByText("Geometry will appear after the first persisted revision.")).toBeInTheDocument();
  });

  it("uses friendly revision chip labels", () => {
    const session: DesignThreadSessionV1 = {
      schemaVersion: 1,
      updatedAt: "2026-01-01T00:00:00Z",
      activeRunName: "run-0001",
      selectedRevision: { runName: "run-0001", revisionName: "rev-002" },
      messages: [],
      runs: [
        {
          runName: "run-0001",
          runId: "uuid",
          prompt: "cube",
          submittedPrompt: "cube",
          createdAt: "2026-01-01T00:00:00Z",
          statusUrl: "",
          eventsUrl: "",
          eventCursor: 0,
          snapshot: { ...snapshot, current_revision_name: "rev-002", revisions: ["rev-001", "rev-002"] },
          events: [],
          reviewSummary: null,
          artifactRoles: []
        }
      ]
    };

    render(
      <RevisionTimeline
        session={session}
        selected={session.selectedRevision}
        onSelect={vi.fn()}
      />
    );

    expect(screen.getByText("Revision 1")).toBeInTheDocument();
    expect(screen.getByText("Revision 2")).toBeInTheDocument();
    expect(screen.queryByText("run-0001")).not.toBeInTheDocument();
  });

  it("hides internal artifact roles in the menu", async () => {
    render(
      <ArtifactMenu
        runName="run-0001"
        revisionName="rev-001"
        roles={["step", "glb", "build_metadata", "inspect_summary", "view_front"]}
      />
    );

    await userEvent.click(screen.getByText("Artifacts"));

    expect(screen.getByText("STEP")).toBeInTheDocument();
    expect(screen.getByText("GLB")).toBeInTheDocument();
    expect(screen.getByText("View front")).toBeInTheDocument();
    expect(screen.queryByText("build metadata")).not.toBeInTheDocument();
  });
});
