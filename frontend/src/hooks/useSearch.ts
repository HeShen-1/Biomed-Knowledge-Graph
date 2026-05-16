import { useQuery } from '@tanstack/react-query';
import { searchEntities } from '@/api/search';
import { useSearchStore } from '@/store/searchStore';

export function useSearch() {
  const query = useSearchStore((s) => s.query);
  const selectedType = useSearchStore((s) => s.selectedType);

  return useQuery({
    queryKey: ['search', query, selectedType],
    queryFn: () => searchEntities(query, selectedType ?? undefined),
    enabled: query.length >= 2,
    staleTime: 30_000,
  });
}
