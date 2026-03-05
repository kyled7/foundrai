import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  theme: 'dark' | 'light';
  commandPaletteOpen: boolean;
  toggleSidebar: () => void;
  toggleTheme: () => void;
  setCommandPalette: (open: boolean) => void;
}

export const useUI = create<UIState>((set) => ({
  sidebarOpen: true,
  theme: 'dark',
  commandPaletteOpen: false,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  toggleTheme: () => set((s) => {
    const next = s.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.classList.toggle('dark', next === 'dark');
    return { theme: next };
  }),
  setCommandPalette: (open) => set({ commandPaletteOpen: open }),
}));
