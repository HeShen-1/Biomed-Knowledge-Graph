import { create } from 'zustand';

interface UiState {
  sidebarOpen: boolean;
  darkMode: boolean;
  toasts: string[];
  toggleSidebar: () => void;
  toggleDarkMode: () => void;
  addToast: (msg: string) => void;
  removeToast: (index: number) => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: true,
  darkMode: false,
  toasts: [],
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  toggleDarkMode: () => set((s) => ({ darkMode: !s.darkMode })),
  addToast: (msg) => set((s) => ({ toasts: [...s.toasts, msg] })),
  removeToast: (index) => set((s) => ({ toasts: s.toasts.filter((_, i) => i !== index) })),
}));
