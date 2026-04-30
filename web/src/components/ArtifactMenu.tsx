import { Download, FileCode2, FileJson, FileText, Image, Layers3 } from "lucide-react";

import { artifactHref } from "../api";

interface ArtifactMenuProps {
  runName: string | null;
  revisionName: string | null;
  roles: string[];
}

const ROLE_LABELS: Record<string, string> = {
  step: "STEP",
  glb: "GLB",
  render_sheet: "Render sheet",
  model_py: "Source",
  review: "Review",
  manifest: "Manifest",
  revision: "Revision"
};

function iconFor(role: string) {
  if (role === "model_py") {
    return <FileCode2 size={15} aria-hidden="true" />;
  }
  if (role === "manifest" || role === "review" || role === "revision") {
    return <FileJson size={15} aria-hidden="true" />;
  }
  if (role === "render_sheet" || role.startsWith("view_")) {
    return <Image size={15} aria-hidden="true" />;
  }
  if (role === "glb") {
    return <Layers3 size={15} aria-hidden="true" />;
  }
  return <FileText size={15} aria-hidden="true" />;
}

export function labelForRole(role: string): string {
  if (ROLE_LABELS[role]) {
    return ROLE_LABELS[role];
  }
  if (role.startsWith("view_")) {
    return `View ${role.slice(5).replaceAll("_", " ")}`;
  }
  return role.replaceAll("_", " ");
}

export function ArtifactMenu({ runName, revisionName, roles }: ArtifactMenuProps) {
  const sorted = roles
    .filter((role) => role !== "revision")
    .filter(isUserFacingRole)
    .sort((a, b) => labelForRole(a).localeCompare(labelForRole(b)));
  const disabled = !runName || !revisionName || sorted.length === 0;

  return (
    <details className="artifact-menu">
      <summary aria-disabled={disabled}>
        <Download size={16} aria-hidden="true" />
        Artifacts
      </summary>
      <div className="artifact-popover">
        {disabled ? (
          <span className="muted">No artifacts yet</span>
        ) : (
          sorted.map((role) => (
            <a
              key={role}
              href={artifactHref(runName, revisionName, role)}
              download
              className="artifact-link"
            >
              {iconFor(role)}
              {labelForRole(role)}
            </a>
          ))
        )}
      </div>
    </details>
  );
}

function isUserFacingRole(role: string): boolean {
  return (
    role === "step" ||
    role === "glb" ||
    role === "render_sheet" ||
    role === "model_py" ||
    role === "manifest" ||
    role === "review" ||
    role.startsWith("view_")
  );
}
