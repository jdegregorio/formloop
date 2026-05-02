import {
  AlertCircle,
  CheckCircle2,
  CircleDashed,
  FileSearch,
  Lightbulb,
  RotateCcw
} from "lucide-react";

import type { AssumptionRecord, ReviewSummary, RunSnapshot, RunStatus } from "../types";
import { FormloopMark } from "./FormloopMark";

interface SummaryPaneProps {
  snapshot: RunSnapshot | null;
  review: ReviewSummary | null;
}

export function SummaryPane({ snapshot, review }: SummaryPaneProps) {
  const status = snapshot?.status || "created";

  return (
    <section className="summary-pane" aria-label="Design understanding">
      <div className="summary-header">
        <h2 className="pane-title">Design Understanding</h2>
        <StatusIndicator status={status} />
      </div>

      <div className="summary-content">
        <div className="summary-section">
          <div className="section-label">
            <FileSearch size={15} aria-hidden="true" />
            Current spec
          </div>
          {snapshot && Object.keys(snapshot.current_spec || {}).length > 0 ? (
            <SpecSummary value={snapshot.current_spec} />
          ) : (
            <p className="muted">Spec will appear when the run starts.</p>
          )}
        </div>

        <div className="summary-section">
          <div className="section-label">
            <Lightbulb size={15} aria-hidden="true" />
            Assumptions
          </div>
          {snapshot?.assumptions?.length ? (
            <Assumptions assumptions={snapshot.assumptions} />
          ) : (
            <p className="muted">No assumptions recorded.</p>
          )}
        </div>

        <div className="summary-section review-summary">
          <div className="section-label">
            {review?.outcome === "pass" ? (
              <CheckCircle2 size={15} aria-hidden="true" />
            ) : review?.outcome === "revise" ? (
              <RotateCcw size={15} aria-hidden="true" />
            ) : (
              <CircleDashed size={15} aria-hidden="true" />
            )}
            Latest review
          </div>
          {review ? (
            <ReviewBlock review={review} />
          ) : (
            <p className="muted">Review summary will appear after geometry is checked.</p>
          )}
        </div>
      </div>
    </section>
  );
}

function StatusIndicator({ status }: { status: RunStatus }) {
  const label = statusLabel(status);
  const className = `status-pill status-${status}`;

  if (status === "succeeded") {
    return (
      <span className={className}>
        <CheckCircle2 size={14} aria-hidden="true" />
        {label}
      </span>
    );
  }
  if (status === "failed" || status === "cancelled") {
    return (
      <span className={className}>
        <AlertCircle size={14} aria-hidden="true" />
        {label}
      </span>
    );
  }
  return (
    <span className={className}>
      <FormloopMark
        className={status === "running" ? "status-mark is-running" : "status-mark"}
        alt=""
        aria-hidden="true"
      />
      {label}
    </span>
  );
}

function ReviewBlock({ review }: { review: ReviewSummary }) {
  return (
    <div className={`review-block review-${review.outcome} review-decision-${review.decision}`}>
      <div className="review-status-row">
        <span className="review-decision-badge">{reviewStatusLabel(review)}</span>
      </div>
      <div className="review-explanation">
        <p>{formatUiText(review.summary)}</p>
        <p>{formatUiText(review.next_step)}</p>
      </div>
      {review.key_findings?.length ? (
        <div className="review-evidence">
          <span className="review-subsection-label">Evidence</span>
          <ul className="compact-list">
            {review.key_findings.slice(0, 3).map((finding) => (
              <li key={finding}>{formatUiText(finding)}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {review.revision_instructions && review.outcome === "revise" ? (
        <p className="review-note">{formatUiText(review.revision_instructions)}</p>
      ) : null}
    </div>
  );
}

function reviewStatusLabel(review: ReviewSummary): string {
  if (review.outcome === "watch") {
    return "Watch";
  }
  return review.decision === "pass" ? "Pass" : "Revise";
}

function Assumptions({ assumptions }: { assumptions: AssumptionRecord[] }) {
  return (
    <ul className="assumptions compact-list">
      {assumptions.slice(0, 5).map((assumption) => (
        <li key={`${assumption.topic}-${assumption.assumption}`} title={assumption.assumption}>
          {formatUiText(assumption.assumption)}
        </li>
      ))}
    </ul>
  );
}

function SpecSummary({ value }: { value: Record<string, unknown> }) {
  const name = formatValue(value.name);
  const intent = formatValue(value.design_intent ?? value.intent);
  const features = Array.isArray(value.features) ? value.features : [];
  const visibleFeatures = features.slice(0, 4);
  const hiddenFeatureCount = Math.max(0, features.length - visibleFeatures.length);

  return (
    <dl className="spec-list spec-list-concise">
      <div>
        <dt>Name</dt>
        <dd>{name}</dd>
      </div>
      <div>
        <dt>Intent</dt>
        <dd>{intent}</dd>
      </div>
      <div>
        <dt>Features</dt>
        <dd>
          {features.length ? (
            <ul className="spec-feature-list">
              {visibleFeatures.map((feature, index) => (
                <li key={`${index}-${formatValue(feature)}`}>{formatValue(feature)}</li>
              ))}
              {hiddenFeatureCount ? (
                <li className="muted">+{hiddenFeatureCount} more feature(s)</li>
              ) : null}
            </ul>
          ) : (
            "Not specified"
          )}
        </dd>
      </div>
    </dl>
  );
}

function statusLabel(status: RunStatus): string {
  if (status === "created") {
    return "Idle";
  }
  if (status === "running") {
    return "Running";
  }
  if (status === "succeeded") {
    return "Complete";
  }
  if (status === "cancelled") {
    return "Cancelled";
  }
  return "Failed";
}

function formatUiText(value: string): string {
  return value.replace(/\b-?\d+\.\d{4,}\b/g, (match) => {
    const rounded = Number.parseFloat(match).toFixed(3);
    return rounded.replace(/\.?0+$/, "");
  });
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "Not specified";
  }
  if (Array.isArray(value)) {
    return value.map(formatValue).join(", ");
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return formatUiText(String(value));
}
