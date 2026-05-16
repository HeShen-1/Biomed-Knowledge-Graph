import { describe, it, expect } from 'vitest';
import { useSearchStore } from '@/store/searchStore';

describe('searchStore', () => {
  it('sets and clears query', () => {
    useSearchStore.getState().setQuery('BRCA1');
    expect(useSearchStore.getState().query).toBe('BRCA1');
    useSearchStore.getState().clearSearch();
    expect(useSearchStore.getState().query).toBe('');
  });

  it('sets selectedType', () => {
    useSearchStore.getState().setSelectedType('gene');
    expect(useSearchStore.getState().selectedType).toBe('gene');
    useSearchStore.getState().setSelectedType(null);
    expect(useSearchStore.getState().selectedType).toBeNull();
  });
});
