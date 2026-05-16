import { useQuery } from '@tanstack/react-query';
import { expandNode } from '@/api/graph';

export function useGraphExpand(type: string | null, id: string | null, depth = 1) {
  return useQuery({
    queryKey: ['expand', type, id, depth],
    queryFn: () => expandNode(type!, id!, depth),
    enabled: type !== null && id !== null,
  });
}
