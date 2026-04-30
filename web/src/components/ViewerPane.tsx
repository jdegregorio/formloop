import { artifactHref } from "../api";
import { artifactRolesFromSnapshot } from "../session";
import type { DesignThreadSessionV1, RunRecord } from "../types";
import { ArtifactMenu } from "./ArtifactMenu";
import { GLBViewer } from "./GLBViewer";
import { RevisionTimeline } from "./RevisionTimeline";

interface ViewerPaneProps {
  session: DesignThreadSessionV1;
  selected: { runName: string; revisionName: string } | null;
  selectedRun: RunRecord | null;
  onSelectRevision: (selection: { runName: string; revisionName: string }) => void;
}

export function ViewerPane({
  session,
  selected,
  selectedRun,
  onSelectRevision
}: ViewerPaneProps) {
  const glbSrc =
    selected?.runName && selected?.revisionName
      ? artifactHref(selected.runName, selected.revisionName, "glb")
      : null;
  const artifactRoles = Array.from(
    new Set([
      ...(selectedRun?.artifactRoles || []),
      ...(selectedRun?.snapshot ? artifactRolesFromSnapshot(selectedRun.snapshot) : [])
    ])
  );

  return (
    <section className="viewer-pane" aria-label="Geometry viewer">
      <div className="viewer-toolbar">
        <h2 className="pane-title">Geometry</h2>
        <div className="viewer-actions">
          <ArtifactMenu
            runName={selected?.runName || null}
            revisionName={selected?.revisionName || null}
            roles={artifactRoles}
          />
        </div>
      </div>
      <RevisionTimeline
        session={session}
        selected={selected}
        onSelect={onSelectRevision}
      />
      <GLBViewer src={glbSrc} />
    </section>
  );
}
