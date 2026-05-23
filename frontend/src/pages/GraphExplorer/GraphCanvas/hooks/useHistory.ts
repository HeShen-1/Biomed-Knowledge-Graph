import { useCallback } from 'react';
import type { Core } from 'cytoscape';
import { useUiStore } from '@/store/uiStore';
import { useGraphStore } from '@/store/graphStore';

export function useHistory(cy: Core | null) {
  const history = useUiStore((s) => s.history);
  const historyIndex = useUiStore((s) => s.historyIndex);
  const pushHistory = useUiStore((s) => s.pushHistory);
  const undoHistory = useUiStore((s) => s.undo);
  const redoHistory = useUiStore((s) => s.redo);
  const selectedNodeIds = useUiStore((s) => s.selectedNodeIds);

  const graphNodes = useGraphStore((s) => s.nodes);
  const graphEdges = useGraphStore((s) => s.edges);

  const canUndo = historyIndex >= 0 && history.length > 0;
  const canRedo = historyIndex < history.length - 1;

  const push = useCallback(
    (action: string, description: string) => {
      pushHistory({
        action,
        description,
        selectedNodeIds: [...selectedNodeIds],
        nodeCount: graphNodes.length,
        edgeCount: graphEdges.length,
      });
    },
    [pushHistory, selectedNodeIds, graphNodes.length, graphEdges.length],
  );

  const undo = useCallback(() => {
    const entry = undoHistory();
    if (!entry) return;
    useUiStore.getState().selectNodes(entry.selectedNodeIds);
  }, [undoHistory]);

  const redo = useCallback(() => {
    const entry = redoHistory();
    if (!entry) return;
    useUiStore.getState().selectNodes(entry.selectedNodeIds);
  }, [redoHistory]);

  return { pushHistory: push, undo, redo, canUndo, canRedo, history, historyIndex };
}
