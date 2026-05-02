import type {
  ArtifactManifest,
  EventPage,
  ReferenceImageUploadResponse,
  ReviewSummary,
  RunCreateResponse,
  RunSnapshot
} from "./types";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = response.statusText;
    try {
      const payload = (await response.json()) as { detail?: string };
      message = payload.detail || message;
    } catch {
      // Keep the HTTP status text when the server did not return JSON.
    }
    throw new ApiError(response.status, message);
  }
  return (await response.json()) as T;
}

export async function createRun(input: {
  prompt: string;
  reference_image?: string;
  profile?: string;
}): Promise<RunCreateResponse> {
  return parseJson<RunCreateResponse>(
    await fetch("/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: input.prompt,
        profile: input.profile || "normal",
        reference_image: input.reference_image || null
      })
    })
  );
}

export async function uploadReferenceImage(
  file: File
): Promise<ReferenceImageUploadResponse> {
  validateReferenceImage(file);
  const form = new FormData();
  form.append("file", file);
  return parseJson<ReferenceImageUploadResponse>(
    await fetch("/reference-images", {
      method: "POST",
      body: form
    })
  );
}

export async function fetchSnapshot(runName: string): Promise<RunSnapshot> {
  return parseJson<RunSnapshot>(await fetch(`/runs/${encodeURIComponent(runName)}/snapshot`));
}

export async function fetchEvents(runName: string, since: number): Promise<EventPage> {
  return parseJson<EventPage>(
    await fetch(`/runs/${encodeURIComponent(runName)}/events?since=${since}`)
  );
}

export async function fetchReviewSummary(runName: string): Promise<ReviewSummary | null> {
  const response = await fetch(`/runs/${encodeURIComponent(runName)}/review-summary`);
  if (response.status === 404) {
    return null;
  }
  return normalizeReviewSummary(await parseJson<unknown>(response));
}

export async function fetchArtifactManifest(
  runName: string,
  revisionName: string
): Promise<ArtifactManifest | null> {
  const response = await fetch(artifactHref(runName, revisionName, "manifest"));
  if (response.status === 404) {
    return null;
  }
  return parseJson<ArtifactManifest>(response);
}

export function artifactHref(runName: string, revisionName: string, role: string): string {
  return `/runs/${encodeURIComponent(runName)}/revisions/${encodeURIComponent(
    revisionName
  )}/artifacts/${encodeURIComponent(role)}`;
}

export function revisionHref(runName: string, revisionName: string): string {
  return `/runs/${encodeURIComponent(runName)}/revisions/${encodeURIComponent(revisionName)}`;
}

export function validateReferenceImage(file: File): void {
  const accepted = new Set(["image/png", "image/jpeg"]);
  if (!accepted.has(file.type)) {
    throw new Error("Reference image must be a PNG or JPEG.");
  }
  if (file.size > 10 * 1024 * 1024) {
    throw new Error("Reference image must be 10 MB or smaller.");
  }
}

export function normalizeReviewSummary(payload: unknown): ReviewSummary {
  if (!payload || typeof payload !== "object") {
    throw new Error("Review summary response was not an object.");
  }
  const data = payload as Record<string, unknown>;
  if (data.schema_version === 1) {
    const decision = data.decision === "pass" ? "pass" : "revise";
    const keyFindings = asStringArray(data.key_findings);
    const suspectFeatures = asStringArray(data.suspect_or_missing_features);
    const suspectDimensions = asStringArray(data.suspect_dimensions_to_recheck);
    const revisionInstructions = asText(data.revision_instructions);
    const summary =
      firstText(keyFindings) ||
      firstText(suspectFeatures) ||
      firstText(suspectDimensions) ||
      revisionInstructions ||
      (decision === "pass" ? "Review accepted this revision." : "Review requested changes.");

    return {
      schema_version: 2,
      decision,
      outcome: decision,
      summary,
      next_step:
        decision === "pass"
          ? "Deliver this design."
          : revisionInstructions || "Revise the design using the review findings.",
      key_findings: [...keyFindings, ...suspectFeatures, ...suspectDimensions],
      revision_instructions: revisionInstructions
    };
  }

  return data as unknown as ReviewSummary;
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.map((item) => String(item).trim()).filter(Boolean)
    : [];
}

function asText(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function firstText(values: string[]): string {
  return values.find(Boolean) || "";
}
