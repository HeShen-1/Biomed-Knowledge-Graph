import { useEffect, useRef, useCallback, useMemo, useState } from 'react';
import cytoscape, { type Core, type ElementDefinition } from 'cytoscape';
import { animate } from 'animejs';
import { useCytoscapeState } from '@/hooks/useCytoscapeState';
import { useKeyboard } from './keyboard';
import { useBoxSelect } from './hooks/useBoxSelect';
import { BoxSelector } from './BoxSelector';

const TYPE_COLORS: Record<string, string> = {
  gene: '#0f62fe', protein: '#24a148', compound: '#da1e28',
  disease: '#f1c21b', article: '#8b949e',
};

const TYPE_DIMS: Record<string, number> = {
  gene: 26, protein: 24, compound: 22, disease: 28, article: 18,
};

function shortLabel(raw: string, max = 18): string {
  if (!raw) return '';
  return raw.length > max ? raw.slice(0, max - 1) + '…' : raw;
}

interface CytoscapeRendererProps {
  onReady?: (cy: Core) => void;
}

export function CytoscapeRenderer({ onReady }: CytoscapeRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [cy, setCy] = useState<Core | null>(null);
  const prevNodeIdsRef = useRef<Set<string>>(new Set());
  const handleSelectRef = useRef<((evt: cytoscape.EventObject) => void) | null>(null);
  const { nodes, edges, layout, setSelectedNode, theme } = useCytoscapeState();

  useKeyboard(cy);
  const { rect: boxRect } = useBoxSelect(cy);

  const dark = theme === 'dark';
  const canvasBg = dark ? '#0d1117' : '#ffffff';
  const labelColor = dark ? '#c9cdd4' : '#444444';
  const edgeColor = dark ? '#30363d' : '#c0c0c0';
  const selectedBorder = dark ? '#ffffff' : '#161616';
  const textOutline = dark ? '#0d1117' : '#ffffff';

  const handleSelect = useCallback((evt: cytoscape.EventObject) => {
    const node = evt.target;
    const pos = node.renderedPosition();

    if (cy) {
      const el = cy.container();
      if (el) {
        const rect = el.getBoundingClientRect();
        animate('__cyRipple', {
          duration: 0,
          onComplete: () => {
            const ripple = document.createElement('div');
            ripple.style.cssText = `
              position:absolute; pointer-events:none; z-index:10;
              left:${pos.x - 16 + rect.left - el.offsetLeft}px;
              top:${pos.y - 16 + rect.top - el.offsetTop}px;
              width:32px; height:32px; border-radius:50%;
              border:2px solid #fff; opacity:0.8;
            `;
            el.appendChild(ripple);
            animate(ripple, {
              scale: [1, 3.5],
              opacity: [0.8, 0],
              duration: 600,
              easing: 'easeOutExpo',
              onComplete: () => ripple.remove(),
            });
          },
        });
      }
    }

    setSelectedNode({
      id: node.id(),
      type: node.data('type') ?? 'unknown',
      properties: {
        label: node.data('label'),
        name: node.data('name'),
        symbol: node.data('symbol'),
        description: node.data('description'),
      },
    });
  }, [cy, setSelectedNode]);

  // Keep a ref to the latest handleSelect so the cy event listener never goes stale
  handleSelectRef.current = handleSelect;

  useEffect(() => {
    if (!containerRef.current || cy) return;
    const instance = cytoscape({
      container: containerRef.current,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#0f62fe',
            'label': 'data(label)',
            'font-size': '11px',
            'font-family': 'IBM Plex Sans, sans-serif',
            'font-weight': 500,
            'color': labelColor,
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 4,
            'text-wrap': 'ellipsis',
            'text-max-width': '70px',
            'min-zoomed-font-size': '7px',
            'border-width': '1.5px',
            'border-color': canvasBg,
            'width': 24,
            'height': 24,
          },
        },
        ...Object.entries(TYPE_COLORS).map(([type, color]) => ({
          selector: `node[type="${type}"]`,
          style: {
            'background-color': color,
            'width': TYPE_DIMS[type] ?? 24,
            'height': TYPE_DIMS[type] ?? 24,
          },
        })),
        {
          selector: 'node[type="compound"]',
          style: {
            'shape': 'diamond',
            'background-color': '#8a3ffc',
            'border-color': '#b379f9',
            'border-width': '2px',
            'width': 34,
            'height': 34,
            'font-size': '10px',
            'font-weight': 'bold',
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': '4px',
            'border-color': selectedBorder,
            'text-outline-width': '4px',
            'text-outline-color': textOutline,
          },
        },
        {
          selector: 'edge',
          style: {
            'line-color': edgeColor,
            'width': 1.0,
            'target-arrow-color': edgeColor,
            'target-arrow-shape': 'triangle',
            'arrow-scale': 0.7,
            'curve-style': 'bezier',
            'label': 'data(relation)',
            'font-size': '7px',
            'color': edgeColor,
            'text-opacity': 0.5,
            'text-rotation': 'autorotate',
          },
        },
        {
          selector: 'edge[relation="INTERACTS_WITH"]',
          style: { 'line-color': '#1f6feb33', 'width': 1.2 },
        },
        {
          selector: 'edge[relation="BINDS_TO"]',
          style: { 'line-color': '#da1e2833', 'width': 1.0 },
        },
        {
          selector: 'edge[relation="TARGETS"]',
          style: { 'line-color': '#f1c21b33', 'width': 1.0 },
        },
      ],
      layout: { name: 'cose' },
    });
    setCy(instance);
    onReady?.(instance);

    const onTap = (evt: cytoscape.EventObject) => {
      handleSelectRef.current?.(evt);
    };
    instance.on('tap', 'node', onTap);
    return () => { instance.destroy(); setCy(null); };
  }, []);

  // Update theme-dependent styles
  useEffect(() => {
    if (!cy) return;
    cy.style()
      .selector('node')
      .style({ 'color': labelColor, 'text-outline-color': textOutline, 'border-color': canvasBg })
      .selector('node:selected')
      .style({ 'border-color': selectedBorder, 'text-outline-color': textOutline })
      .selector('edge')
      .style({ 'line-color': edgeColor, 'target-arrow-color': edgeColor })
      .update();
  }, [theme, canvasBg, labelColor, edgeColor, selectedBorder, textOutline]);

  // Build elements array, memoized to avoid recreation on every render
  const elements: ElementDefinition[] = useMemo(() => {
    if (nodes.length === 0) return [];

    return [
      ...nodes.map(n => {
        const props = (n.properties ?? {}) as Record<string, unknown>;
        const label = shortLabel(String(props?.label ?? props?.name ?? props?.symbol ?? n.id));
        const dim = TYPE_DIMS[n.type] ?? 24;
        return {
          group: 'nodes' as const,
          data: {
            id: n.id, type: n.type, label, dim,
            name: props?.name ?? '',
            symbol: props?.symbol ?? '',
            description: props?.description ?? '',
          },
        };
      }),
      ...edges
        .map((e, i) => {
          const srcId = (e as any).source_id || e.node?.id || '';
          const tgtId = (e as any).target_id || '';
          if (!srcId || !tgtId) return null;
          return {
            group: 'edges' as const,
            data: {
              id: `e${i}-${srcId.slice(-12)}-${tgtId.slice(-12)}`,
              source: srcId,
              target: tgtId,
              relation: e.relation,
            },
          };
        })
        .filter(Boolean) as ElementDefinition[],
    ];
  }, [nodes, edges]);

  useEffect(() => {
    if (!cy) return;

    if (elements.length === 0) {
      // Only clear if we had previous content (prevents flash during loading transitions)
      if (prevNodeIdsRef.current.size > 0) {
        cy.elements().remove();
        prevNodeIdsRef.current = new Set();
      }
      return;
    }

    const newNodeIds = new Set(nodes.map(n => n.id));
    const oldIds = prevNodeIdsRef.current;
    const isSuperset = oldIds.size > 0 && [...oldIds].every(id => newNodeIds.has(id));

    if (isSuperset) {
      // Incremental update: only add new nodes/edges, don't rebuild entire graph
      const newNodes = elements.filter(el => el.group === 'nodes' && !oldIds.has(el.data.id!));
      const newEdges = elements.filter(el => el.group === 'edges');
      if (newNodes.length > 0 || newEdges.length > 0) {
        cy.batch(() => {
          if (newNodes.length > 0) cy.add(newNodes);
          if (newEdges.length > 0) cy.add(newEdges);
        });
        const doAnimate = layout !== 'grid';
        cy.layout({ name: layout, animate: doAnimate, animationDuration: doAnimate ? 500 : 0 } as any).run();
      }
    } else {
      // Full replacement: graph structure changed (different root node)
      const doAnimate = layout !== 'grid';
      // Scatter initial positions near center to avoid (0,0) cluster on replacement
      const cx = cy.width() / 2;
      const cyH = cy.height() / 2;
      const scatteredElements = elements.map(el => {
        if (el.group === 'nodes') {
          return {
            ...el,
            position: {
              x: cx + (Math.random() - 0.5) * 120,
              y: cyH + (Math.random() - 0.5) * 120,
            },
          };
        }
        return el;
      });
      cy.batch(() => {
        cy.json({ elements: scatteredElements });
      });
      cy.layout({
        name: layout,
        animate: doAnimate,
        animationDuration: doAnimate ? 600 : 0,
        easing: 'ease-out',
      } as any).run();
    }

    prevNodeIdsRef.current = newNodeIds;
  }, [elements, layout]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', minHeight: 480 }}>
      <div
        ref={containerRef}
        style={{
          width: '100%',
          height: '100%',
          minHeight: 480,
          background: canvasBg,
          borderRadius: 'var(--radius-md)',
          transition: 'background 0.35s ease',
        }}
      />
      <BoxSelector rect={boxRect} />
    </div>
  );
}
