import { useEffect, useRef } from 'react';
import { animate, stagger } from 'animejs';
import type { Suggestion } from '@/api/search';

const BADGE_CLASS: Record<string, string> = {
  gene: 'badge badge-gene',
  protein: 'badge badge-protein',
  compound: 'badge badge-compound',
  disease: 'badge badge-disease',
  article: 'badge badge-article',
};

interface Props {
  items: Suggestion[];
  onSelect: (item: Suggestion) => void;
  visible: boolean;
}

export function SuggestionList({ items, onSelect, visible }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!visible || !containerRef.current) return;

    const rows = containerRef.current.querySelectorAll<HTMLElement>('.sug-row');
    const tl = animate(Array.from(rows), {
      translateX: [8, 0],
      opacity: [0, 1],
      delay: stagger(20),
      duration: 250,
      easing: 'easeOutCubic',
    });

    return () => {
      tl.pause();
    };
  }, [visible, items]);

  if (!visible || items.length === 0) return null;

  return (
    <div ref={containerRef} style={{
      marginTop: 6,
      border: '1px solid var(--color-hairline)',
      borderRadius: 'var(--radius-md)',
      background: 'var(--color-surface-2)',
      maxHeight: 260,
      overflowY: 'auto',
    }}>
      {items.map((item, i) => (
        <div
          key={item.id}
          className="sug-row"
          role="option"
          aria-selected={i === 0}
          onClick={() => onSelect(item)}
          style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '8px 12px', cursor: 'pointer',
            borderBottom: i < items.length - 1 ? '1px solid var(--color-hairline)' : 'none',
            opacity: 0,
          }}
        >
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-ink)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {item.label}
            </div>
          </div>
          <span className={BADGE_CLASS[item.type] ?? 'badge'}>
            {item.type}
          </span>
        </div>
      ))}
    </div>
  );
}
