import { useShallow } from 'zustand/react/shallow';
import { useGraphStore } from '@/store/graphStore';
import { useThemeStore } from '@/store/themeStore';

export function useCytoscapeState() {
  const { nodes, edges, layout } = useGraphStore(
    useShallow((s) => ({ nodes: s.nodes, edges: s.edges, layout: s.layout })),
  );
  const setSelectedNode = useGraphStore((s) => s.setSelectedNode);
  const theme = useThemeStore((s) => s.theme);

  return { nodes, edges, layout, setSelectedNode, theme };
}
