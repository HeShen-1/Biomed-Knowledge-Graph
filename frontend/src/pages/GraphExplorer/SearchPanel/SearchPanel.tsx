import { useGraphStore } from '@/store/graphStore';
import { useSearch } from '@/hooks/useSearch';
import { SearchInput } from './SearchInput';
import { SuggestionList } from './SuggestionList';
import { FilterBar } from './FilterBar';
import type { Suggestion } from '@/api/search';

export function SearchPanel() {
  const { query, setQuery, selectedType, setSelectedType, data: results, isLoading, isError } = useSearch();
  const setSelectedNode = useGraphStore((s) => s.setSelectedNode);

  const handleSelect = (item: Suggestion) => {
    setSelectedNode({ id: item.id, type: item.type, properties: {} });
  };

  return (
    <div className="card" style={{ padding: 'var(--space-3)' }}>
      <div className="panel-header" style={{ marginBottom: 0, paddingBottom: 'var(--space-2)' }}>
        <h3>Search</h3>
        {isLoading && (
          <span style={{ fontSize: 11, color: 'var(--color-ink-subtle)', fontFamily: 'var(--font-mono)' }}>
            searching…
          </span>
        )}
      </div>

      <SearchInput value={query} onChange={setQuery} />
      <FilterBar selectedType={selectedType} onChange={setSelectedType} />

      {isError && (
        <div style={{ marginTop: 8, fontSize: 12, color: 'var(--color-error)', display: 'flex', alignItems: 'center', gap: 6 }}>
          <span>⚠</span> Search failed
        </div>
      )}

      <SuggestionList
        items={results?.map((r) => ({ id: r.id, type: r.type, label: r.label })) ?? []}
        onSelect={handleSelect}
        visible={query.length >= 1 && !isLoading}
      />
    </div>
  );
}
