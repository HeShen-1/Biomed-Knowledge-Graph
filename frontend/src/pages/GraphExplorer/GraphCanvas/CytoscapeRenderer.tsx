import { useEffect, useRef, useCallback } from 'react';
import cytoscape, { type Core, type ElementDefinition } from 'cytoscape';
import { useGraphStore } from '@/store/graphStore';

const TYPE_COLORS: Record<string, string> = {
  gene: '#0f62fe', protein: '#24a148', compound: '#da1e28',
  disease: '#f1c21b', article: '#8c8c8c',
};

export function CytoscapeRenderer() {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const nodes = useGraphStore((s) => s.nodes);
  const edges = useGraphStore((s) => s.edges);
  const layout = useGraphStore((s) => s.layout);
  const setSelectedNode = useGraphStore((s) => s.setSelectedNode);

  const handleSelect = useCallback((evt: cytoscape.EventObject) => {
    const node = evt.target;
    setSelectedNode({
      id: node.id(),
      type: node.data('type') ?? 'unknown',
      properties: { label: node.data('label') },
    });
  }, [setSelectedNode]);

  useEffect(() => {
    if (!containerRef.current || cyRef.current) return;
    cyRef.current = cytoscape({
      container: containerRef.current,
      style: [
        { selector: 'node', style: { 'background-color': '#0f62fe', label: 'data(label)', 'font-size': '10px', 'text-valign': 'bottom', 'text-halign': 'center' } },
        ...Object.entries(TYPE_COLORS).map(([type, color]) => ({ selector: `node[type="${type}"]`, style: { 'background-color': color } })),
        { selector: 'edge', style: { 'line-color': '#e0e0e0', width: 1, 'target-arrow-color': '#e0e0e0', 'target-arrow-shape': 'triangle' } },
      ],
    });
    cyRef.current.on('tap', 'node', handleSelect);
    return () => { cyRef.current?.destroy(); cyRef.current = null; };
  }, [handleSelect]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy || nodes.length === 0) return;
    const elements: ElementDefinition[] = [
      ...nodes.map(n => ({ group: 'nodes' as const, data: { id: n.id, type: n.type, label: (n.properties as Record<string,unknown>)?.label ?? n.id } })),
      ...edges.map(e => {
        const srcId = e.node?.id ?? '';
        const tgtId = (e.properties as Record<string,unknown>)?.target_id as string ?? '';
        if (!srcId || !tgtId) return null;
        return { group: 'edges' as const, data: { id: `${srcId}-${tgtId}-${e.relation}`, source: srcId, target: tgtId, label: e.relation } };
      }).filter(Boolean) as ElementDefinition[],
    ];
    cy.json({ elements });
    cy.layout({ name: layout }).run();
  }, [nodes, edges, layout]);

  return <div ref={containerRef} style={{ width: '100%', height: 500, border: '1px solid var(--color-hairline)', borderRadius: 'var(--radius-md)' }} />;
}
