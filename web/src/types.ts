export type RunStatus = "created" | "running" | "succeeded" | "failed" | "cancelled";
export type ReviewDecision = "pass" | "revise";
export type ReviewOutcome = "revise" | "watch" | "pass";

export interface AgentAnswer {
  schema_version: number;
  text: string;
  delivered_revision_name: string | null;
}

export interface AssumptionRecord {
  schema_version: number;
  topic: string;
  assumption: string;
  recorded_at: string;
}

export interface SnapshotArtifacts {
  schema_version: number;
  step_path: string | null;
  glb_path: string | null;
  render_sheet_path: string | null;
  view_paths: string[];
}

export interface RunSnapshot {
  schema_version: number;
  run_id: string;
  run_name: string;
  status: RunStatus;
  input_summary: string;
  status_detail: string | null;
  generated_at: string;
  current_spec: Record<string, unknown>;
  current_revision_name: string | null;
  delivered_revision_name: string | null;
  revisions: string[];
  assumptions: AssumptionRecord[];
  research_findings: Array<Record<string, unknown>>;
  effective_role_runtimes: Record<string, Record<string, string>>;
  final_answer: AgentAnswer | null;
  latest_review_decision: ReviewDecision | null;
  latest_review_summary_path: string | null;
  artifacts: SnapshotArtifacts;
  last_event_index: number;
  last_event_kind: string | null;
  last_message: string | null;
  latest_narration: string | null;
  latest_narration_index: number | null;
  latest_narration_phase: string | null;
}

export interface ProgressEvent {
  schema_version: number;
  index: number;
  kind: string;
  ts: string;
  message: string;
  phase: string | null;
  narration_error: string | null;
  data: Record<string, unknown>;
}

export interface ReviewSummary {
  schema_version: number;
  decision: ReviewDecision;
  outcome: ReviewOutcome;
  summary: string;
  next_step: string;
  key_findings: string[];
  revision_instructions: string;
}

export interface RunCreateResponse {
  schema_version: number;
  run_id: string;
  run_name: string;
  status_url: string;
  events_url: string;
}

export interface ReferenceImageUploadResponse {
  schema_version: number;
  upload_id: string;
  reference_image: string;
  filename: string;
  content_type: string;
  size_bytes: number;
}

export interface ArtifactEntry {
  schema_version: number;
  role: string;
  path: string;
  format: string;
  required: boolean;
  sha256: string | null;
  size_bytes: number | null;
}

export interface ArtifactManifest {
  schema_version: number;
  revision_name: string;
  entries: ArtifactEntry[];
}

export interface EventPage {
  events: ProgressEvent[];
  next_since: number;
}

export interface AttachmentMeta {
  name: string;
  contentType: string;
  sizeBytes: number;
  uploadId?: string;
}

export interface ThreadMessage {
  id: string;
  role: "user" | "agent";
  text: string;
  createdAt: string;
  runName?: string;
  attachment?: AttachmentMeta;
}

export interface RunRecord {
  runName: string;
  runId: string;
  prompt: string;
  submittedPrompt: string;
  createdAt: string;
  statusUrl: string;
  eventsUrl: string;
  eventCursor: number;
  snapshot: RunSnapshot | null;
  events: ProgressEvent[];
  reviewSummary: ReviewSummary | null;
  artifactRoles: string[];
}

export interface DesignThreadSessionV1 {
  schemaVersion: 1;
  updatedAt: string;
  activeRunName: string | null;
  selectedRevision: { runName: string; revisionName: string } | null;
  messages: ThreadMessage[];
  runs: RunRecord[];
}
