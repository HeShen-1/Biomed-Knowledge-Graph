import { describe, it, expect } from 'vitest';
import { useGraphStore } from '@/store/graphStore';

describe('graphStore', () => {
  it('sets and clears graph', () => {
    useGraphStore.getState().setSelectedNode({ id: 'gene:BRCA1', type: 'gene', properties: {} });
    expect(useGraphStore.getState().selectedNode?.id).toBe('gene:BRCA1');
    useGraphStore.getState().clearGraph();
    expect(useGraphStore.getState().selectedNode).toBeNull();
  });

  it('changes layout', () => {
    useGraphStore.getState().setLayout('breadthfirst');
    expect(useGraphStore.getState().layout).toBe('breadthfirst');
    useGraphStore.getState().setLayout('cose');
  });
});
