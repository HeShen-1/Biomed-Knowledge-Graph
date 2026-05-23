import { useEffect, useRef, useCallback } from 'react';
import { animate, stagger } from 'animejs';
import { useUiStore } from '@/store/uiStore';

function relativeTime(ts: number): string {
  const diff = Date.now() - ts;
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return 'just now';
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  return `${Math.floor(hr / 24)}d ago`;
}

const ACTION_ICONS: Record<string, string> = {
  search: '\u{1F50D}',
  expand: '\u{2795}',
  select: '\u{1F4CC}',
  clear: '\u{1F5D1}',
  collapse: '\u{25C0}',
  undo: '\u{21A9}',
  redo: '\u{21AA}',
};

function actionIcon(action: string): string {
  return ACTION_ICONS[action] ?? '\u{2022}';
}

export function HistoryPanel() {
  const history = useUiStore((s) => s.history);
  const historyIndex = useUiStore((s) => s.historyIndex);
  const undo = useUiStore((s) => s.undo);
  const redo = useUiStore((s) => s.redo);
  const selectNodes = useUiStore((s) => s.selectNodes);

  const listRef = useRef<HTMLDivElement>(null);
  const prevLenRef = useRef(history.length);

  const canUndo = historyIndex >= 0 && history.length > 0;
  const canRedo = historyIndex < history.length - 1;

  useEffect(() => {
    if (!listRef.current) return;
    const items = listRef.current.querySelectorAll<HTMLElement>('.hist-entry');
    const newItems = [...items].slice(prevLenRef.current);
    prevLenRef.current = history.length;

    if (newItems.length === 0) return;

    animate(newItems, {
      translateX: [20, 0],
      opacity: [0, 1],
      duration: 300,
      easing: 'easeOutExpo',
      delay: stagger(40),
    });
  }, [history.length]);

  const jumpTo = useCallback(
    (targetIndex: number) => {
      if (targetIndex === historyIndex) return;
      if (targetIndex < historyIndex) {
        let steps = historyIndex - targetIndex;
        while (steps > 0) {
          undo();
          steps--;
        }
      } else {
        let steps = targetIndex - historyIndex;
        while (steps > 0) {
          redo();
          steps--;
        }
      }
    },
    [historyIndex, undo, redo],
  );

  const handleUndo = useCallback(() => {
    const entry = undo();
    if (entry) selectNodes(entry.selectedNodeIds);
  }, [undo, selectNodes]);

  const handleRedo = useCallback(() => {
    const entry = redo();
    if (entry) selectNodes(entry.selectedNodeIds);
  }, [redo, selectNodes]);

  return (
    <div
      className="card"
      style={{ padding: 'var(--space-3)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}
    >
      <div className="panel-header" style={{ marginBottom: 0, paddingBottom: 'var(--space-2)' }}>
        <h3>History</h3>
        <span style={{ fontSize: 11, color: 'var(--color-ink-subtle)', fontFamily: "'IBM Plex Mono', monospace" }}>
          {history.length > 0 ? `${historyIndex + 1}/${history.length}` : '0'}
        </span>
      </div>

      {history.length === 0 ? (
        <div
          style={{
            textAlign: 'center',
            padding: 'var(--space-5) 0',
            color: 'var(--color-ink-subtle)',
            fontSize: 13,
            fontWeight: 300,
          }}
        >
          No history yet
        </div>
      ) : (
        <div
          ref={listRef}
          style={{
            maxHeight: 300,
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: 1,
          }}
        >
          {history.map((entry, i) => {
            const isPast = i < historyIndex;
            const isCurrent = i === historyIndex;
            const isFuture = i > historyIndex;

            return (
              <button
                key={entry.id}
                className="hist-entry"
                onClick={() => jumpTo(i)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-2)',
                  width: '100%',
                  textAlign: 'left',
                  padding: '8px 10px',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  borderLeft: isCurrent ? '3px solid var(--color-primary)' : '3px solid transparent',
                  background: isCurrent ? 'var(--color-primary-muted)' : 'transparent',
                  fontWeight: isCurrent ? 500 : 400,
                  color: isFuture
                    ? 'var(--color-ink-subtle)'
                    : isPast
                      ? 'var(--color-ink-muted)'
                      : 'var(--color-ink)',
                  fontStyle: isFuture ? 'italic' : 'normal',
                  opacity: isFuture ? 0.55 : isPast ? 0.7 : 1,
                  cursor: 'pointer',
                }}
              >
                <span style={{ fontSize: 13, flexShrink: 0, width: 20, textAlign: 'center' }}>
                  {actionIcon(entry.action)}
                </span>
                <span style={{ fontSize: 12, flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {entry.description}
                </span>
                <span
                  style={{
                    fontSize: 10,
                    color: 'var(--color-ink-subtle)',
                    fontFamily: "'IBM Plex Mono', monospace",
                    flexShrink: 0,
                  }}
                >
                  {relativeTime(entry.timestamp)}
                </span>
              </button>
            );
          })}
        </div>
      )}

      <div
        style={{
          display: 'flex',
          gap: 'var(--space-2)',
          paddingTop: 'var(--space-2)',
          borderTop: '1px solid var(--color-hairline)',
        }}
      >
        <button
          onClick={handleUndo}
          disabled={!canUndo}
          style={{
            flex: 1,
            fontSize: 12,
            padding: '6px 0',
            opacity: canUndo ? 1 : 0.4,
            cursor: canUndo ? 'pointer' : 'not-allowed',
          }}
        >
          Undo
        </button>
        <button
          onClick={handleRedo}
          disabled={!canRedo}
          style={{
            flex: 1,
            fontSize: 12,
            padding: '6px 0',
            opacity: canRedo ? 1 : 0.4,
            cursor: canRedo ? 'pointer' : 'not-allowed',
          }}
        >
          Redo
        </button>
      </div>
    </div>
  );
}
