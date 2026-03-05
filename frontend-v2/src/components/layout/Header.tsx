import { Menu, Moon, Sun, Command } from 'lucide-react';
import { useUI } from '@/stores/ui';

export function Header() {
  const { toggleSidebar, toggleTheme, theme, setCommandPalette } = useUI();

  return (
    <header className="h-14 border-b border-border flex items-center justify-between px-4 bg-card">
      <div className="flex items-center gap-3">
        <button onClick={toggleSidebar} className="md:hidden text-muted hover:text-foreground">
          <Menu size={20} />
        </button>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => setCommandPalette(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-muted bg-background border border-border rounded-md hover:text-foreground"
        >
          <Command size={12} />
          <span>Ctrl+K</span>
        </button>
        <button onClick={toggleTheme} className="p-2 text-muted hover:text-foreground rounded-md hover:bg-border/50">
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </header>
  );
}
