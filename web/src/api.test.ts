import { describe, expect, it, vi } from "vitest";

import {
  ApiError,
  artifactHref,
  createRun,
  normalizeReviewSummary,
  validateReferenceImage
} from "./api";

describe("api client", () => {
  it("constructs stable artifact URLs from roles", () => {
    expect(artifactHref("run-0001", "rev-001", "model_py")).toBe(
      "/runs/run-0001/revisions/rev-001/artifacts/model_py"
    );
  });

  it("posts create-run payloads as JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          schema_version: 1,
          run_id: "uuid",
          run_name: "run-0001",
          status_url: "/runs/run-0001/snapshot",
          events_url: "/runs/run-0001/events"
        }),
        { status: 201, headers: { "Content-Type": "application/json" } }
      )
    );
    vi.stubGlobal("fetch", fetchMock);

    await createRun({ prompt: "cube", reference_image: "/tmp/ref.png", profile: "dev_test" });

    expect(fetchMock).toHaveBeenCalledWith(
      "/runs",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: "cube",
          profile: "dev_test",
          reference_image: "/tmp/ref.png"
        })
      })
    );
  });

  it("surfaces server errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "no snapshot" }), {
          status: 404,
          headers: { "Content-Type": "application/json" }
        })
      )
    );

    await expect(createRun({ prompt: "cube" })).rejects.toThrow(ApiError);
  });

  it("validates browser reference images before upload", () => {
    expect(() =>
      validateReferenceImage(new File(["x"], "ref.gif", { type: "image/gif" }))
    ).toThrow("PNG or JPEG");
    expect(() =>
      validateReferenceImage(new File(["x"], "ref.png", { type: "image/png" }))
    ).not.toThrow();
  });

  it("normalizes legacy review summaries", () => {
    const review = normalizeReviewSummary({
      schema_version: 1,
      decision: "revise",
      confidence: 0.8,
      key_findings: ["hole spacing is off"],
      suspect_or_missing_features: ["missing countersink"],
      suspect_dimensions_to_recheck: [],
      revision_instructions: "Move the holes outward."
    });

    expect(review.schema_version).toBe(2);
    expect(review.outcome).toBe("revise");
    expect(review.summary).toBe("hole spacing is off");
    expect(review.next_step).toBe("Move the holes outward.");
    expect(review.key_findings).toContain("missing countersink");
  });
});
