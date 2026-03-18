import { Menu, Moon, Sun, Monitor, Command } from 'lucide-react';
import { useUI } from '@/stores/ui';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';

export function Header() {
  const { toggleSidebar, toggleTheme, theme, setCommandPalette, breadcrumbs } = useUI();

  const themeIcon = theme === 'dark' ? Sun : theme === 'light' ? Moon : Monitor;
  const ThemeIcon = themeIcon;
  const themeLabel = theme === 'dark' ? 'Switch to light mode' : theme === 'light' ? 'Switch to system theme' : 'Switch to dark mode';

  return (
    <header role="banner" className="h-14 border-b border-border flex items-center justify-between px-4 bg-card">
      <div className="flex items-center gap-3">
        <button
          onClick={toggleSidebar}
          className="md:hidden text-muted hover:text-foreground min-h-[44px] min-w-[44px] flex items-center justify-center"
          aria-label="Toggle sidebar"
        >
          <Menu size={20} />
        </button>
        <Breadcrumbs items={breadcrumbs} />
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => setCommandPalette(true)}
          aria-label="Open command palette"
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-muted bg-background border border-border rounded-md hover:text-foreground"
        >
          <Command size={12} />
          <span>Ctrl+K</span>
        </button>
        <button
          onClick={toggleTheme}
          aria-label={themeLabel}
          className="p-2 text-muted hover:text-foreground rounded-md hover:bg-border/50"
        >
          <ThemeIcon size={18} />
        </button>
      </div>
    </header>
  );
}
