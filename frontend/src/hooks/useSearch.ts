import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { searchEntities, getSuggestions } from '@/api/search';
import { useSearchStore } from '@/store/searchStore';

export function useSearch() {
  const query = useSearchStore((s) => s.query);
  const setQuery = useSearchStore((s) => s.setQuery);
  const selectedType = useSearchStore((s) => s.selectedType);
  const setSelectedType = useSearchStore((s) => s.setSelectedType);
  const [debouncedQuery, setDebouncedQuery] = useState(query);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 250);
    return () => clearTimeout(timer);
  }, [query]);

  // Use suggest (ILIKE partial match) for short queries, full-text for longer
  const isShort = debouncedQuery.length >= 1 && debouncedQuery.length < 3;
  const useSuggest = isShort && !selectedType;

  const suggestQuery = useQuery({
    queryKey: ['suggest', debouncedQuery],
    queryFn: () => getSuggestions(debouncedQuery),
    enabled: useSuggest,
    staleTime: 10_000,
  });

  const searchQuery = useQuery({
    queryKey: ['search', debouncedQuery, selectedType],
    queryFn: () => searchEntities(debouncedQuery, selectedType ?? undefined),
    enabled: debouncedQuery.length >= 3 || (debouncedQuery.length >= 1 && !!selectedType),
    staleTime: 30_000,
  });

  const data = useSuggest ? suggestQuery.data : searchQuery.data;
  const isLoading = useSuggest ? suggestQuery.isLoading : searchQuery.isLoading;
  const isError = useSuggest ? suggestQuery.isError : searchQuery.isError;

  return { query, setQuery, selectedType, setSelectedType, data, isLoading, isError };
}
