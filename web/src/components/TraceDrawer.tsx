import { Activity, AlertCircle } from "lucide-react";

import type { ProgressEvent } from "../types";

interface TraceDrawerProps {
  events: ProgressEvent[];
}

export function TraceDrawer({ events }: TraceDrawerProps) {
  return (
    <details className="trace-drawer">
      <summary>
        <Activity size={16} aria-hidden="true" />
        Trace
        <span>{events.length}</span>
      </summary>
      <div className="trace-list">
        {events.length === 0 ? (
          <p className="muted">No events yet</p>
        ) : (
          events.map((event) => (
            <div className="trace-row" key={event.index}>
              <span className={`trace-dot trace-${event.phase || event.kind}`} />
              <div>
                <div className="trace-meta">
                  <span>{event.phase || "event"}</span>
                  <span>{event.kind}</span>
                  <span>#{event.index}</span>
                </div>
                {event.message ? <p>{event.message}</p> : null}
                {event.narration_error ? (
                  <p className="trace-error">
                    <AlertCircle size={14} aria-hidden="true" />
                    {event.narration_error}
                  </p>
                ) : null}
              </div>
            </div>
          ))
        )}
      </div>
    </details>
  );
}
