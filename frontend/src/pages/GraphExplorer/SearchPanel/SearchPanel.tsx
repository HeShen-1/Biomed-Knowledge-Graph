import { useSearchStore } from '@/store/searchStore';
import { useGraphStore } from '@/store/graphStore';
import { useSearch } from '@/hooks/useSearch';
import { SearchInput } from './SearchInput';
import { SuggestionList } from './SuggestionList';
import { FilterBar } from './FilterBar';
import type { Suggestion } from '@/api/search';

export function SearchPanel() {
  const setQuery = useSearchStore((s) => s.setQuery);
  const query = useSearchStore((s) => s.query);
  const setSelectedType = useSearchStore((s) => s.setSelectedType);
  const selectedType = useSearchStore((s) => s.selectedType);
  const setSelectedNode = useGraphStore((s) => s.setSelectedNode);
  const { data: results, isLoading, isError } = useSearch();

  const handleSelect = (item: Suggestion) => {
    setSelectedNode({ id: item.id, type: item.type, properties: {} });
  };

  return (
    <div className="card" style={{ marginBottom: 'var(--space-3)' }}>
      <h3 style={{ fontWeight: 300, marginBottom: 'var(--space-2)' }}>Search</h3>
      <SearchInput value={query} onChange={setQuery} />
      <FilterBar selectedType={selectedType} onChange={setSelectedType} />
      {isLoading && <p style={{ color: 'var(--color-ink-subtle)', fontSize: 12, marginTop: 4 }}>Searching...</p>}
      {isError && <p style={{ color: 'var(--color-error)', fontSize: 12, marginTop: 4 }}>Search failed</p>}
      <SuggestionList
        items={results?.map((r) => ({ id: r.id, type: r.type, label: r.label })) ?? []}
        onSelect={handleSelect}
        visible={query.length >= 2 && !isLoading}
      />
    </div>
  );
}
