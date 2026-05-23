import { useEffect, useRef } from 'react';
import { createTimeline } from 'animejs';
import { SearchPanel } from './SearchPanel/SearchPanel';
import { GraphCanvas } from './GraphCanvas/GraphCanvas';
import { DetailPanel } from './DetailPanel/DetailPanel';
import { HistoryPanel } from './DetailPanel/HistoryPanel';
import { ThemeToggle } from './ThemeToggle';
import { ErrorBoundary } from './ErrorBoundary';

export function GraphExplorer() {
  const headerRef = useRef<HTMLDivElement>(null);
  const leftRef = useRef<HTMLDivElement>(null);
  const centerRef = useRef<HTMLDivElement>(null);
  const rightRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Staggered page load animation using animejs v4
    const tl = createTimeline();
    tl.add(headerRef.current!, { opacity: [0, 1], translateY: [-24, 0], duration: 400, easing: 'easeOutExpo' })
      .add(leftRef.current!, { opacity: [0, 1], translateX: [-20, 0], duration: 450, easing: 'easeOutExpo' }, '+=50')
      .add(centerRef.current!, { opacity: [0, 1], scale: [0.97, 1], duration: 450, easing: 'easeOutExpo' }, '-=300')
      .add(rightRef.current!, { opacity: [0, 1], translateX: [20, 0], duration: 450, easing: 'easeOutExpo' }, '-=300');
  }, []);

  return (
    <div style={{ minHeight: '100vh', background: 'var(--color-canvas)', display: 'flex', flexDirection: 'column' }}>
      {/* App header */}
      <header
        ref={headerRef}
        style={{
          padding: '10px 24px',
          borderBottom: '1px solid var(--color-hairline)',
          background: 'var(--color-surface-1)',
          display: 'flex', alignItems: 'center', gap: 12,
          opacity: 0,
        }}
      >
        <span style={{
          width: 28, height: 28, borderRadius: 6,
          background: 'var(--color-primary)', color: 'var(--color-on-primary)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 15, fontWeight: 500, flexShrink: 0,
        }}>B</span>
        <span style={{ fontWeight: 300, fontSize: 16, letterSpacing: '-0.01em', color: 'var(--color-ink)' }}>
          Biomed <strong style={{ fontWeight: 500 }}>Graph</strong>
        </span>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 11, color: 'var(--color-ink-subtle)', fontFamily: "'IBM Plex Mono', monospace" }}>
            v0.1.0
          </span>
          <ThemeToggle />
        </div>
      </header>

      {/* Main layout */}
      <div style={{
        flex: 1, display: 'grid',
        gridTemplateColumns: '320px 1fr 340px',
        gap: 16, padding: 16, minHeight: 0,
      }}>
        <div ref={leftRef} style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column', opacity: 0 }}>
          <ErrorBoundary>
            <SearchPanel />
          </ErrorBoundary>
        </div>
        <div ref={centerRef} style={{ minHeight: 0, opacity: 0 }}>
          <ErrorBoundary>
            <GraphCanvas />
          </ErrorBoundary>
        </div>
        <div ref={rightRef} style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column', gap: 16, opacity: 0 }}>
          <ErrorBoundary>
            <DetailPanel />
          </ErrorBoundary>
          <ErrorBoundary>
            <HistoryPanel />
          </ErrorBoundary>
        </div>
      </div>
    </div>
  );
}
