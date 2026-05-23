import { create } from 'zustand';

interface HistoryEntry {
  id: string;
  action: string;
  description: string;
  timestamp: number;
  selectedNodeIds: string[];
  nodeCount: number;
  edgeCount: number;
}

interface UiState {
  sidebarOpen: boolean;
  toasts: string[];
  toggleSidebar: () => void;
  addToast: (msg: string) => void;
  removeToast: (index: number) => void;

  selectedNodeIds: string[];
  selectNodes: (ids: string[]) => void;
  deselectNodes: (ids: string[]) => void;
  toggleNodeSelection: (id: string) => void;
  clearSelection: () => void;

  history: HistoryEntry[];
  historyIndex: number;
  pushHistory: (entry: Omit<HistoryEntry, 'id' | 'timestamp'>) => void;
  undo: () => HistoryEntry | null;
  redo: () => HistoryEntry | null;

  collapsedGroups: Record<string, string[]>;
  collapseNeighbors: (centerNodeId: string, neighborIds: string[], groupId: string) => void;
  expandGroup: (groupId: string) => string[];
}

const MAX_HISTORY = 50;

export const useUiStore = create<UiState>((set, get) => ({
  sidebarOpen: true,
  toasts: [],
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  addToast: (msg) => set((s) => ({ toasts: [...s.toasts, msg] })),
  removeToast: (index) => set((s) => ({ toasts: s.toasts.filter((_, i) => i !== index) })),

  selectedNodeIds: [],
  selectNodes: (ids) => set({ selectedNodeIds: [...ids] }),
  deselectNodes: (ids) =>
    set((s) => ({ selectedNodeIds: s.selectedNodeIds.filter((id) => !ids.includes(id)) })),
  toggleNodeSelection: (id) =>
    set((s) => ({
      selectedNodeIds: s.selectedNodeIds.includes(id)
        ? s.selectedNodeIds.filter((x) => x !== id)
        : [...s.selectedNodeIds, id],
    })),
  clearSelection: () => set({ selectedNodeIds: [] }),

  history: [],
  historyIndex: -1,
  pushHistory: (entry) =>
    set((s) => {
      const newEntry: HistoryEntry = {
        ...entry,
        id: crypto.randomUUID(),
        timestamp: Date.now(),
      };
      const truncated = s.history.slice(0, s.historyIndex + 1);
      const updated = [...truncated, newEntry];
      if (updated.length > MAX_HISTORY) {
        updated.shift();
      }
      return { history: updated, historyIndex: updated.length - 1 };
    }),
  undo: () => {
    const { history, historyIndex } = get();
    if (historyIndex < 0 || historyIndex >= history.length) return null;
    set({ historyIndex: historyIndex - 1 });
    return history[historyIndex]!;
  },
  redo: () => {
    const { history, historyIndex } = get();
    if (historyIndex >= history.length - 1) return null;
    const nextIndex = historyIndex + 1;
    set({ historyIndex: nextIndex });
    return history[nextIndex]!;
  },

  collapsedGroups: {},
  collapseNeighbors: (_centerNodeId, neighborIds, groupId) =>
    set((s) => ({
      collapsedGroups: { ...s.collapsedGroups, [groupId]: [...neighborIds] },
    })),
  expandGroup: (groupId) => {
    const { collapsedGroups } = get();
    const hiddenIds = collapsedGroups[groupId] ?? [];
    const next = { ...collapsedGroups };
    delete next[groupId];
    set({ collapsedGroups: next });
    return hiddenIds;
  },
}));
