import { create } from 'zustand';
import type { Suggestion } from '@/api/search';

interface SearchState {
  query: string;
  suggestions: Suggestion[];
  selectedType: string | null;
  setQuery: (q: string) => void;
  setSuggestions: (items: Suggestion[]) => void;
  setSelectedType: (t: string | null) => void;
  clearSearch: () => void;
}

export const useSearchStore = create<SearchState>((set) => ({
  query: '',
  suggestions: [],
  selectedType: null,
  setQuery: (query) => set({ query }),
  setSuggestions: (suggestions) => set({ suggestions }),
  setSelectedType: (selectedType) => set({ selectedType }),
  clearSearch: () => set({ query: '', suggestions: [], selectedType: null }),
}));
