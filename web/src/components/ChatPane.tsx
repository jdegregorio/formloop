import { Activity, ArrowUp, ImagePlus, LoaderCircle, X } from "lucide-react";
import type { FormEvent, KeyboardEvent } from "react";

import type { ProgressEvent, ThreadMessage } from "../types";
import { TraceDrawer } from "./TraceDrawer";

interface ChatPaneProps {
  messages: ThreadMessage[];
  activeRunName?: string | null;
  prompt: string;
  attachment: File | null;
  submitting: boolean;
  error: string | null;
  latestNarration: string | null;
  latestNarrationPhase: string | null;
  events: Parameters<typeof TraceDrawer>[0]["events"];
  onPromptChange: (value: string) => void;
  onAttachmentChange: (file: File | null) => void;
  onSubmit: () => void;
}

export function ChatPane({
  messages,
  activeRunName,
  prompt,
  attachment,
  submitting,
  error,
  latestNarration,
  latestNarrationPhase,
  events,
  onPromptChange,
  onAttachmentChange,
  onSubmit
}: ChatPaneProps) {
  const narrationItems = narrationHistory(events, latestNarration, latestNarrationPhase);
  const narrationAnchorId = [...messages]
    .reverse()
    .find((message) => message.role === "agent" && (!activeRunName || message.runName === activeRunName))
    ?.id;
  const hasNestedNarration = Boolean(narrationAnchorId && narrationItems.length > 0);

  function submit(event: FormEvent) {
    event.preventDefault();
    onSubmit();
  }

  function handlePromptKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== "Enter" || event.shiftKey || event.nativeEvent.isComposing) {
      return;
    }
    event.preventDefault();
    if (!submitting && prompt.trim()) {
      onSubmit();
    }
  }

  return (
    <section className="chat-pane" aria-label="Input">
      <div className="chat-header">
        <h1 className="pane-title">Input</h1>
      </div>

      <div className="message-list">
        {messages.length === 0 && narrationItems.length === 0 ? (
          <div className="empty-thread">
            <h2>New request</h2>
            <p>Describe the geometry, fit, and constraints for the first pass.</p>
          </div>
        ) : (
          messages.map((message) => (
            <article className={`message message-${message.role}`} key={message.id}>
              {message.id === narrationAnchorId ? (
                <NarrationHistory items={narrationItems} defaultOpen={false} />
              ) : null}
              <p>{message.text}</p>
              {message.attachment ? (
                <span className="attachment-tag">{message.attachment.name}</span>
              ) : null}
            </article>
          ))
        )}
        {!hasNestedNarration && narrationItems.length > 0 ? (
          <NarrationHistory items={narrationItems} defaultOpen />
        ) : null}
      </div>

      <TraceDrawer events={events} />

      <form className="composer" onSubmit={submit}>
        {error ? <p className="form-error">{error}</p> : null}
        {attachment ? (
          <div className="attachment-preview">
            <span>{attachment.name}</span>
            <button type="button" onClick={() => onAttachmentChange(null)} title="Remove image">
              <X size={16} aria-hidden="true" />
            </button>
          </div>
        ) : null}
        <textarea
          value={prompt}
          onChange={(event) => onPromptChange(event.target.value)}
          onKeyDown={handlePromptKeyDown}
          placeholder="A 60 mm mounting plate with two countersunk holes..."
          rows={4}
        />
        <div className="composer-actions">
          <label className="icon-button" title="Attach reference image">
            <ImagePlus size={18} aria-hidden="true" />
            <input
              type="file"
              accept="image/png,image/jpeg"
              onChange={(event) => onAttachmentChange(event.target.files?.[0] || null)}
            />
          </label>
          <button className="send-button" type="submit" disabled={submitting || !prompt.trim()}>
            {submitting ? (
              <LoaderCircle className="spin" size={18} aria-hidden="true" />
            ) : (
              <ArrowUp size={18} aria-hidden="true" />
            )}
            Send
          </button>
        </div>
      </form>
    </section>
  );
}

interface NarrationItem {
  id: string;
  index: number | null;
  phase: string;
  message: string;
}

function NarrationHistory({
  items,
  defaultOpen
}: {
  items: NarrationItem[];
  defaultOpen?: boolean;
}) {
  if (items.length === 0) {
    return null;
  }

  return (
    <details className="narration-history" open={defaultOpen}>
      <summary>
        <Activity size={16} aria-hidden="true" />
        <span>Progress updates</span>
        <span className="narration-count">{items.length}</span>
      </summary>
      <ol className="narration-list">
        {items.map((item) => (
          <li className="narration-item" key={item.id}>
            <span className="narration-phase">{item.phase}</span>
            <p>{item.message}</p>
          </li>
        ))}
      </ol>
    </details>
  );
}

function narrationHistory(
  events: ProgressEvent[],
  latestNarration: string | null,
  latestNarrationPhase: string | null
): NarrationItem[] {
  const items: NarrationItem[] = events
    .filter((event) => event.kind === "narration" && event.message.trim())
    .map((event) => ({
      id: `event-${event.index}`,
      index: event.index,
      phase: event.phase || "progress",
      message: event.message.trim()
    }));

  const latest = latestNarration?.trim();
  if (latest && !items.some((item) => item.message === latest)) {
    items.push({
      id: "latest-narration",
      index: null,
      phase: latestNarrationPhase || "progress",
      message: latest
    });
  }

  return items.sort((a, b) => (a.index ?? Number.MAX_SAFE_INTEGER) - (b.index ?? Number.MAX_SAFE_INTEGER));
}
