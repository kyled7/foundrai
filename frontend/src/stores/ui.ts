import { create } from 'zustand';
import type { BreadcrumbItem } from '@/lib/types';

export type Theme = 'dark' | 'light' | 'system';

interface UIState {
  sidebarOpen: boolean;
  theme: Theme;
  commandPaletteOpen: boolean;
  breadcrumbs: BreadcrumbItem[];
  toggleSidebar: () => void;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
  setCommandPalette: (open: boolean) => void;
  setBreadcrumbs: (items: BreadcrumbItem[]) => void;
}

function resolveTheme(theme: Theme): 'dark' | 'light' {
  if (theme === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return theme;
}

function applyTheme(theme: Theme) {
  const resolved = resolveTheme(theme);
  document.documentElement.classList.toggle('dark', resolved === 'dark');
  localStorage.setItem('foundrai-theme', theme);
}

const savedTheme = (localStorage.getItem('foundrai-theme') as Theme) || 'dark';
applyTheme(savedTheme);

// Listen for system theme changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
  const current = localStorage.getItem('foundrai-theme') as Theme;
  if (current === 'system') {
    applyTheme('system');
  }
});

export const useUI = create<UIState>((set) => ({
  sidebarOpen: true,
  theme: savedTheme,
  commandPaletteOpen: false,
  breadcrumbs: [],
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setTheme: (theme) => {
    applyTheme(theme);
    set({ theme });
  },
  toggleTheme: () => set((s) => {
    const order: Theme[] = ['dark', 'light', 'system'];
    const next = order[(order.indexOf(s.theme) + 1) % order.length];
    applyTheme(next);
    return { theme: next };
  }),
  setCommandPalette: (open) => set({ commandPaletteOpen: open }),
  setBreadcrumbs: (items) => set({ breadcrumbs: items }),
}));
