import { useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { expandNode } from '@/api/graph';
import { useGraphStore } from '@/store/graphStore';

export function useGraphExpand(type: string | null, id: string | null, depth = 1) {
  const setSubgraph = useGraphStore((s) => s.setSubgraph);
  const prevKeyRef = useRef<string>('');

  const key = type && id ? `${type}:${id}:${depth}` : '';
  const enabled = type !== null && id !== null;

  const query = useQuery({
    queryKey: ['expand', type, id, depth],
    queryFn: () => expandNode(type!, id!, depth),
    enabled,
    staleTime: 0,
  });

  useEffect(() => {
    if (!query.data || query.data.nodes.length === 0) return;
    if (key === prevKeyRef.current) return;

    prevKeyRef.current = key;
    setSubgraph(query.data.nodes, query.data.edges || []);
  }, [query.data, key, setSubgraph]);

  return query;
}
