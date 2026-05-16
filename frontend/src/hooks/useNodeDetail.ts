import { useQuery } from '@tanstack/react-query';
import { getNodeDetail } from '@/api/graph';

export function useNodeDetail(type: string | null, id: string | null) {
  return useQuery({
    queryKey: ['node', type, id],
    queryFn: () => getNodeDetail(type!, id!),
    enabled: type !== null && id !== null,
  });
}
