import { useEffect, useState, useCallback, useRef } from 'react';
import { animate } from 'animejs';
import type { Core, EventObject, NodeSingular } from 'cytoscape';
import { useUiStore } from '@/store/uiStore';
import { useGraphStore } from '@/store/graphStore';

interface CompoundNodeProps {
  cy: Core | null;
}

interface ContextMenuState {
  x: number;
  y: number;
  nodeId: string;
  neighborCount: number;
}

export function CompoundNode({ cy }: CompoundNodeProps) {
  const [menu, setMenu] = useState<ContextMenuState | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const collapseNeighbors = useUiStore((s) => s.collapseNeighbors);
  const expandGroup = useUiStore((s) => s.expandGroup);
  const layout = useGraphStore((s) => s.layout);

  useEffect(() => {
    if (!cy) return;

    const handleCxttap = (evt: EventObject) => {
      const node = evt.target;
      if (!node.isNode() || node.data('type') === 'compound') return;

      const nodeId = node.id();
      const groupId = `group-${nodeId}`;
      const { collapsedGroups } = useUiStore.getState();
      if (collapsedGroups[groupId]) return;

      const neighborhood = node.closedNeighborhood();
      const neighbors = neighborhood.difference(node).filter((n: NodeSingular) => n.isNode());
      const count = neighbors.length;
      if (count === 0) return;

      setMenu({
        x: (evt.originalEvent as MouseEvent).clientX,
        y: (evt.originalEvent as MouseEvent).clientY,
        nodeId,
        neighborCount: count,
      });
    };

    cy.on('cxttap', 'node', handleCxttap);
    return () => { cy.off('cxttap', 'node', handleCxttap); };
  }, [cy]);

  useEffect(() => {
    if (!menu) return;

    const close = () => setMenu(null);
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close();
    };
    const onClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        close();
      }
    };

    document.addEventListener('keydown', onKeyDown);
    const timer = setTimeout(() => document.addEventListener('click', onClick), 0);
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.removeEventListener('click', onClick);
      clearTimeout(timer);
    };
  }, [menu]);

  useEffect(() => {
    if (menu && menuRef.current) {
      animate(menuRef.current, {
        opacity: [0, 1],
        translateY: [-4, 0],
        duration: 200,
        easing: 'easeOutExpo',
      });
    }
  }, [menu]);

  const handleCollapse = useCallback(() => {
    if (!menu || !cy) return;

    const nodeId = menu.nodeId;
    const node = cy.getElementById(nodeId);
    const neighborhood = node.closedNeighborhood();
    const neighbors = neighborhood.difference(node).filter((n) => n.isNode());
    const neighborIds = neighbors.map((n) => n.id());
    const groupId = `group-${nodeId}`;

    let cx = 0, cyPos = 0;
    neighbors.forEach((n) => {
      const p = n.position();
      cx += p.x;
      cyPos += p.y;
    });
    cx /= neighborIds.length;
    cyPos /= neighborIds.length;

    cy.batch(() => {
      neighbors.forEach((n) => {
        n.connectedEdges().style('display', 'none');
        n.style('display', 'none');
      });
      cy.add({
        group: 'nodes',
        data: {
          id: groupId,
          type: 'compound',
          label: `[+${neighborIds.length}]`,
          collapsedIds: neighborIds,
        },
        position: { x: cx, y: cyPos },
      });
    });

    collapseNeighbors(nodeId, neighborIds, groupId);
    setMenu(null);

    if (layout !== 'grid') {
      cy.layout({ name: layout, animate: true, animationDuration: 500 } as any).run();
    }
  }, [menu, cy, collapseNeighbors, layout]);

  useEffect(() => {
    if (!cy) return;

    const handleDbltap = (evt: EventObject) => {
      const node = evt.target;
      if (!node.isNode() || node.data('type') !== 'compound') return;

      const groupId = node.id();
      const hiddenIds = expandGroup(groupId);
      if (hiddenIds.length === 0) return;

      const compoundPos = { x: node.position('x') as number, y: node.position('y') as number };
      cy.remove(node);

      const validIds: string[] = [];
      cy.batch(() => {
        hiddenIds.forEach((id) => {
          const el = cy.getElementById(id);
          if (el.length > 0) {
            validIds.push(id);
            el.style('display', 'element');
            el.connectedEdges().style('display', 'element');
            el.style('opacity', '0');
          }
        });
      });

      const currentLayout = useGraphStore.getState().layout;
      const runLayout = cy.layout({ name: currentLayout, animate: false } as any);
      runLayout.one('layoutstop', () => {
        const targets = new Map<string, { x: number; y: number }>();
        validIds.forEach((id) => {
          const el = cy.getElementById(id);
          targets.set(id, {
            x: el.position('x') as number,
            y: el.position('y') as number,
          });
          el.position({ x: compoundPos.x, y: compoundPos.y });
        });

        validIds.forEach((id, i) => {
          setTimeout(() => {
            const el = cy.getElementById(id);
            const target = targets.get(id);
            if (el.length > 0 && target) {
              el.animate(
                { position: target, style: { opacity: 1 } },
                { duration: 400, easing: 'ease-out-expo' },
              );
            }
          }, i * 30);
        });
      });
      runLayout.run();
    };

    cy.on('dbltap', 'node[type="compound"]', handleDbltap);
    return () => { cy.off('dbltap', 'node[type="compound"]', handleDbltap); };
  }, [cy, expandGroup]);

  if (!menu) return null;

  return (
    <div
      ref={menuRef}
      style={{
        position: 'fixed',
        left: menu.x,
        top: menu.y,
        zIndex: 1000,
        opacity: 0,
      }}
    >
      <div
        style={{
          background: 'var(--color-surface-3)',
          border: '1px solid var(--color-hairline-strong)',
          borderRadius: '8px',
          padding: '4px',
          minWidth: 210,
          boxShadow: '0 4px 24px rgba(0,0,0,0.35)',
        }}
      >
        <button
          type="button"
          onClick={handleCollapse}
          style={{
            display: 'block',
            width: '100%',
            textAlign: 'left',
            padding: '8px 14px',
            border: 'none',
            borderRadius: '6px',
            background: 'transparent',
            color: 'var(--color-ink)',
            cursor: 'pointer',
            fontSize: 13,
            fontFamily: 'inherit',
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.background = 'var(--color-surface-2)';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.background = 'transparent';
          }}
        >
          Collapse Neighbors ({menu.neighborCount})
        </button>
      </div>
    </div>
  );
}
