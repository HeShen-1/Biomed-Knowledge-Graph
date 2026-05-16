import { useQuery } from '@tanstack/react-query';
import { getProteinNetwork } from '@/api/graph';

export function useProteinNetwork(proteinId: string | null, minScore = 0.7) {
  return useQuery({
    queryKey: ['network', proteinId, minScore],
    queryFn: () => getProteinNetwork(proteinId!, minScore),
    enabled: proteinId !== null,
  });
}
