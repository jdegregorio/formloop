import { GitCommitHorizontal } from "lucide-react";

import type { DesignThreadSessionV1 } from "../types";

interface RevisionTimelineProps {
  session: DesignThreadSessionV1;
  selected: { runName: string; revisionName: string } | null;
  onSelect: (selection: { runName: string; revisionName: string }) => void;
}

export function RevisionTimeline({ session, selected, onSelect }: RevisionTimelineProps) {
  const revisions = session.runs.flatMap((run) =>
    (run.snapshot?.revisions || []).map((revisionName) => ({
      runName: run.runName,
      revisionName,
      status: run.snapshot?.status || "created"
    }))
  );

  return (
    <div className="revision-rail" aria-label="Revisions">
      <div className="section-label">
        <GitCommitHorizontal size={15} aria-hidden="true" />
        Revisions
      </div>
      <div className="revision-list">
        {revisions.length === 0 ? (
          <span className="muted">No revisions yet</span>
        ) : (
          revisions.map((revision) => {
            const active =
              selected?.runName === revision.runName &&
              selected?.revisionName === revision.revisionName;
            return (
              <button
                type="button"
                key={`${revision.runName}-${revision.revisionName}`}
                className={active ? "revision-chip active" : "revision-chip"}
                onClick={() => onSelect(revision)}
                aria-label={`${friendlyRevisionName(revision.revisionName)} from ${revision.runName}`}
              >
                <span>{friendlyRevisionName(revision.revisionName)}</span>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}

function friendlyRevisionName(revisionName: string): string {
  const match = revisionName.match(/(\d+)$/);
  return match ? `Revision ${Number(match[1])}` : "Revision";
}
