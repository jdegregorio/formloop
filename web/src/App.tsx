import { type CSSProperties, useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  createRun,
  fetchArtifactManifest,
  fetchEvents,
  fetchReviewSummary,
  fetchSnapshot,
  uploadReferenceImage,
  validateReferenceImage
} from "./api";
import { ChatPane } from "./components/ChatPane";
import { FormloopMark, FormloopWordmark } from "./components/FormloopMark";
import { SummaryPane } from "./components/SummaryPane";
import { ViewerPane } from "./components/ViewerPane";
import {
  artifactRolesFromSnapshot,
  buildSubmittedPrompt,
  createEmptySession,
  loadSession,
  mergeEvents,
  nowIso,
  saveSession,
  selectedRevisionFromSession,
  upsertFinalMessage,
  upsertRun,
  userFacingArtifactRoles
} from "./session";
import type { DesignThreadSessionV1, RunRecord } from "./types";

function uid(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

const LAYOUT_STORAGE_KEY = "formloop.workspaceLayout.v2";

interface WorkspaceLayout {
  chatPercent: number;
  summaryPercent: number;
}

export function App() {
  const [session, setSession] = useState<DesignThreadSessionV1>(() => loadSession());
  const [layout, setLayout] = useState<WorkspaceLayout>(() => loadWorkspaceLayout());
  const [prompt, setPrompt] = useState("");
  const [attachment, setAttachment] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sessionRef = useRef(session);
  const workspaceRef = useRef<HTMLDivElement | null>(null);
  const rightStackRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    sessionRef.current = session;
    saveSession(session);
  }, [session]);

  useEffect(() => {
    window.localStorage.setItem(LAYOUT_STORAGE_KEY, JSON.stringify(layout));
  }, [layout]);

  const activeRun = useMemo(
    () => session.runs.find((run) => run.runName === session.activeRunName) || null,
    [session]
  );
  const selectedRevision = selectedRevisionFromSession(session);
  const selectedRun = selectedRevision
    ? session.runs.find((run) => run.runName === selectedRevision.runName) || null
    : activeRun;
  const activeSnapshot = activeRun?.snapshot || null;
  const activeReview = activeRun?.reviewSummary || null;
  const activeEvents = activeRun?.events || [];

  const refreshRun = useCallback(async (run: RunRecord): Promise<RunRecord> => {
    const snapshot = await fetchSnapshot(run.runName);
    const eventPage = await fetchEvents(run.runName, run.eventCursor);
    const review = snapshot.current_revision_name ? await fetchReviewSummary(run.runName) : null;
    const manifest = snapshot.current_revision_name
      ? await fetchArtifactManifest(run.runName, snapshot.current_revision_name)
      : null;
    const artifactRoles = manifest
      ? userFacingArtifactRoles(
          snapshot,
          manifest.entries.map((entry) => entry.role)
        )
      : artifactRolesFromSnapshot(snapshot);

    return {
      ...run,
      eventCursor: eventPage.next_since,
      snapshot,
      events: mergeEvents(run.events, eventPage.events),
      reviewSummary: review || run.reviewSummary,
      artifactRoles
    };
  }, []);

  const refreshPending = useCallback(async () => {
    const current = sessionRef.current;
    const pending = current.runs.filter((run) => !isTerminal(run.snapshot?.status));
    if (pending.length === 0) {
      return;
    }
    const refreshed = await Promise.allSettled(pending.map(refreshRun));
    let next = sessionRef.current;
    for (const result of refreshed) {
      if (result.status !== "fulfilled") {
        continue;
      }
      next = upsertRun(next, result.value);
      if (result.value.snapshot?.current_revision_name && !next.selectedRevision) {
        next = {
          ...next,
          selectedRevision: {
            runName: result.value.runName,
            revisionName: result.value.snapshot.current_revision_name
          }
        };
      }
      if (result.value.snapshot?.final_answer) {
        next = upsertFinalMessage(next, result.value.snapshot);
      }
    }
    setSession(next);
  }, [refreshRun]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      void refreshPending();
    }, 1800);
    void refreshPending();
    return () => window.clearInterval(timer);
  }, [refreshPending]);

  async function handleSubmit() {
    const visiblePrompt = prompt.trim();
    if (!visiblePrompt) {
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      let attachmentMeta = undefined;
      let referenceImage = undefined;
      if (attachment) {
        validateReferenceImage(attachment);
        const upload = await uploadReferenceImage(attachment);
        referenceImage = upload.reference_image;
        attachmentMeta = {
          name: attachment.name,
          contentType: attachment.type,
          sizeBytes: attachment.size,
          uploadId: upload.upload_id
        };
      }

      const submittedPrompt = buildSubmittedPrompt(visiblePrompt, activeSnapshot, activeReview);
      const response = await createRun({ prompt: submittedPrompt, reference_image: referenceImage });
      const createdAt = nowIso();
      const runRecord: RunRecord = {
        runName: response.run_name,
        runId: response.run_id,
        prompt: visiblePrompt,
        submittedPrompt,
        createdAt,
        statusUrl: response.status_url,
        eventsUrl: response.events_url,
        eventCursor: 0,
        snapshot: null,
        events: [],
        reviewSummary: null,
        artifactRoles: []
      };
      const next = upsertRun(
        {
          ...sessionRef.current,
          selectedRevision: null,
          messages: [
            ...sessionRef.current.messages,
            {
              id: uid("user"),
              role: "user",
              text: visiblePrompt,
              createdAt,
              runName: response.run_name,
              attachment: attachmentMeta
            }
          ]
        },
        runRecord
      );
      setSession(next);
      setPrompt("");
      setAttachment(null);
      window.setTimeout(() => void refreshPending(), 200);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to submit request.");
    } finally {
      setSubmitting(false);
    }
  }

  function handleAttachmentChange(file: File | null) {
    try {
      if (file) {
        validateReferenceImage(file);
      }
      setAttachment(file);
      setError(null);
    } catch (err) {
      setAttachment(null);
      setError(err instanceof Error ? err.message : "Invalid reference image.");
    }
  }

  function handleSelectRevision(selection: { runName: string; revisionName: string }) {
    setSession((current) => ({ ...current, selectedRevision: selection }));
  }

  function handleClearThread() {
    const empty = createEmptySession();
    setSession(empty);
    setPrompt("");
    setAttachment(null);
    setError(null);
  }

  function startHorizontalResize(event: React.PointerEvent<HTMLDivElement>) {
    event.preventDefault();
    const bounds = workspaceRef.current?.getBoundingClientRect();
    if (!bounds) {
      return;
    }
    const handleMove = (move: PointerEvent) => {
      const percent = ((move.clientX - bounds.left) / bounds.width) * 100;
      setLayout((current) => ({ ...current, chatPercent: clamp(percent, 30, 62) }));
    };
    trackPointer(handleMove);
  }

  function startVerticalResize(event: React.PointerEvent<HTMLDivElement>) {
    event.preventDefault();
    const bounds = rightStackRef.current?.getBoundingClientRect();
    if (!bounds) {
      return;
    }
    const handleMove = (move: PointerEvent) => {
      const percent = ((move.clientY - bounds.top) / bounds.height) * 100;
      setLayout((current) => ({ ...current, summaryPercent: clamp(percent, 26, 68) }));
    };
    trackPointer(handleMove);
  }

  const workspaceStyle = {
    "--chat-pane-width": `${layout.chatPercent}%`,
    "--summary-pane-height": `${layout.summaryPercent}%`
  } as CSSProperties;

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <FormloopMark className="brand-mark" alt="" aria-hidden="true" />
          <div className="brand-copy">
            <FormloopWordmark className="brand-wordmark" />
            <span className="topbar-subtitle">Describe it. Generate it. Refine it.</span>
          </div>
        </div>
        <button className="ghost-button" type="button" onClick={handleClearThread}>
          Start over
        </button>
      </header>
      <div className="workspace" ref={workspaceRef} style={workspaceStyle}>
        <ChatPane
          messages={session.messages}
          activeRunName={activeRun?.runName || null}
          prompt={prompt}
          attachment={attachment}
          submitting={submitting}
          error={error}
          latestNarration={activeSnapshot?.latest_narration || null}
          latestNarrationPhase={activeSnapshot?.latest_narration_phase || null}
          events={activeEvents}
          onPromptChange={setPrompt}
          onAttachmentChange={handleAttachmentChange}
          onSubmit={handleSubmit}
        />
        <div
          className="pane-resizer pane-resizer-vertical"
          role="separator"
          aria-label="Resize requests and preview panes"
          aria-orientation="vertical"
          onPointerDown={startHorizontalResize}
        />
        <div className="right-stack" ref={rightStackRef}>
          <SummaryPane snapshot={activeSnapshot} review={activeReview} />
          <div
            className="pane-resizer pane-resizer-horizontal"
            role="separator"
            aria-label="Resize understanding and geometry panes"
            aria-orientation="horizontal"
            onPointerDown={startVerticalResize}
          />
          <ViewerPane
            session={session}
            selected={selectedRevision}
            selectedRun={selectedRun}
            onSelectRevision={handleSelectRevision}
          />
        </div>
      </div>
    </main>
  );
}

function isTerminal(status: string | undefined): boolean {
  return status === "succeeded" || status === "failed" || status === "cancelled";
}

function loadWorkspaceLayout(): WorkspaceLayout {
  try {
    const raw = window.localStorage.getItem(LAYOUT_STORAGE_KEY);
    if (!raw) {
      return { chatPercent: 34, summaryPercent: 68 };
    }
    const parsed = JSON.parse(raw) as Partial<WorkspaceLayout>;
    return {
      chatPercent: clamp(Number(parsed.chatPercent) || 34, 30, 62),
      summaryPercent: clamp(Number(parsed.summaryPercent) || 68, 26, 68)
    };
  } catch {
    return { chatPercent: 34, summaryPercent: 68 };
  }
}

function trackPointer(handleMove: (event: PointerEvent) => void): void {
  const stop = () => {
    window.removeEventListener("pointermove", handleMove);
    window.removeEventListener("pointerup", stop);
    window.removeEventListener("pointercancel", stop);
    document.body.classList.remove("is-resizing-pane");
  };
  document.body.classList.add("is-resizing-pane");
  window.addEventListener("pointermove", handleMove);
  window.addEventListener("pointerup", stop);
  window.addEventListener("pointercancel", stop);
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}
