import type {
  DesignThreadSessionV1,
  ProgressEvent,
  ReviewSummary,
  RunRecord,
  RunSnapshot
} from "./types";

export const STORAGE_KEY = "formloop.designThread.v1";

interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

export function nowIso(): string {
  return new Date().toISOString();
}

export function createEmptySession(): DesignThreadSessionV1 {
  return {
    schemaVersion: 1,
    updatedAt: nowIso(),
    activeRunName: null,
    selectedRevision: null,
    messages: [],
    runs: []
  };
}

export function loadSession(storage: StorageLike = window.localStorage): DesignThreadSessionV1 {
  const raw = storage.getItem(STORAGE_KEY);
  if (!raw) {
    return createEmptySession();
  }
  try {
    const parsed = JSON.parse(raw) as DesignThreadSessionV1;
    if (parsed.schemaVersion !== 1 || !Array.isArray(parsed.runs)) {
      return createEmptySession();
    }
    return {
      ...createEmptySession(),
      ...parsed,
      messages: Array.isArray(parsed.messages) ? parsed.messages : [],
      runs: parsed.runs
    };
  } catch {
    return createEmptySession();
  }
}

export function saveSession(
  session: DesignThreadSessionV1,
  storage: StorageLike = window.localStorage
): void {
  storage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      ...session,
      updatedAt: nowIso()
    })
  );
}

export function mergeEvents(existing: ProgressEvent[], incoming: ProgressEvent[]): ProgressEvent[] {
  const byIndex = new Map<number, ProgressEvent>();
  for (const event of existing) {
    byIndex.set(event.index, event);
  }
  for (const event of incoming) {
    byIndex.set(event.index, event);
  }
  return [...byIndex.values()].sort((a, b) => a.index - b.index);
}

export function upsertRun(
  session: DesignThreadSessionV1,
  runRecord: RunRecord
): DesignThreadSessionV1 {
  const runs = session.runs.filter((run) => run.runName !== runRecord.runName);
  runs.push(runRecord);
  runs.sort((a, b) => a.createdAt.localeCompare(b.createdAt));
  return { ...session, runs, activeRunName: runRecord.runName };
}

export function upsertFinalMessage(
  session: DesignThreadSessionV1,
  snapshot: RunSnapshot
): DesignThreadSessionV1 {
  if (!snapshot.final_answer?.text) {
    return session;
  }
  const id = `agent-${snapshot.run_name}`;
  const next = session.messages.filter((message) => message.id !== id);
  next.push({
    id,
    role: "agent",
    text: snapshot.final_answer.text,
    createdAt: snapshot.generated_at,
    runName: snapshot.run_name
  });
  next.sort((a, b) => a.createdAt.localeCompare(b.createdAt));
  return { ...session, messages: next };
}

export function buildSubmittedPrompt(
  visiblePrompt: string,
  latestSnapshot: RunSnapshot | null,
  latestReview: ReviewSummary | null
): string {
  if (!latestSnapshot && !latestReview) {
    return visiblePrompt;
  }
  const context = [
    "Follow-up design request:",
    visiblePrompt,
    "",
    "Current design-thread context:",
    latestSnapshot ? `Latest normalized spec:\n${stableJson(latestSnapshot.current_spec)}` : "",
    latestReview ? `Latest review summary:\n${stableJson(latestReview)}` : ""
  ]
    .filter(Boolean)
    .join("\n");
  return `${context}\n\nRevise the design accordingly while preserving any requirements that still apply.`;
}

export function artifactRolesFromSnapshot(snapshot: RunSnapshot): string[] {
  const roles = new Set<string>();
  if (snapshot.current_revision_name) {
    roles.add("manifest");
    roles.add("revision");
  }
  if (snapshot.artifacts.step_path) {
    roles.add("step");
  }
  if (snapshot.artifacts.glb_path) {
    roles.add("glb");
  }
  if (snapshot.artifacts.render_sheet_path) {
    roles.add("render_sheet");
  }
  for (const viewPath of snapshot.artifacts.view_paths || []) {
    const basename = viewPath.split(/[\\/]/).pop() || "";
    const stem = basename.replace(/\.[^.]+$/, "");
    if (stem) {
      roles.add(`view_${stem}`);
    }
  }
  if (snapshot.latest_review_summary_path) {
    roles.add("review");
  }
  roles.add("model_py");
  return [...roles];
}

export function userFacingArtifactRoles(
  snapshot: RunSnapshot,
  manifestRoles: string[] = []
): string[] {
  const roles = new Set(artifactRolesFromSnapshot(snapshot));
  for (const role of manifestRoles) {
    if (isUserFacingArtifactRole(role)) {
      roles.add(role);
    }
  }
  return [...roles].filter(isUserFacingArtifactRole);
}

export function selectedRevisionFromSession(
  session: DesignThreadSessionV1
): { runName: string; revisionName: string } | null {
  if (session.selectedRevision) {
    return session.selectedRevision;
  }
  for (const run of [...session.runs].reverse()) {
    const revision = run.snapshot?.current_revision_name;
    if (revision) {
      return { runName: run.runName, revisionName: revision };
    }
  }
  return null;
}

function stableJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

function isUserFacingArtifactRole(role: string): boolean {
  return (
    role === "step" ||
    role === "glb" ||
    role === "render_sheet" ||
    role === "model_py" ||
    role === "manifest" ||
    role === "review" ||
    role === "revision" ||
    role.startsWith("view_")
  );
}
