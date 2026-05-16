import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { searchEntities } from '@/api/search';
import { useSearchStore } from '@/store/searchStore';

export function useSearch() {
  const query = useSearchStore((s) => s.query);
  const selectedType = useSearchStore((s) => s.selectedType);
  const [debouncedQuery, setDebouncedQuery] = useState(query);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(timer);
  }, [query]);

  return useQuery({
    queryKey: ['search', debouncedQuery, selectedType],
    queryFn: () => searchEntities(debouncedQuery, selectedType ?? undefined),
    enabled: debouncedQuery.length >= 2,
    staleTime: 30_000,
  });
}
