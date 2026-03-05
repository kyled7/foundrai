import { useLocation } from '@tanstack/react-router';
import { LayoutDashboard, FolderKanban, Settings, Blocks, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useUI } from '@/stores/ui';
import { useProjects } from '@/hooks/use-projects';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/templates', label: 'Templates', icon: Blocks },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUI();
  const location = useLocation();
  const { data } = useProjects();

  return (
    <>
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 md:hidden" onClick={toggleSidebar} />
      )}

      <aside
        className={cn(
          'fixed top-0 left-0 z-50 h-full w-64 bg-card border-r border-border flex flex-col transition-transform',
          'md:translate-x-0 md:static md:z-auto',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex items-center justify-between h-14 px-4 border-b border-border">
          <a href="/" className="flex items-center gap-2">
            <span className="text-lg font-bold text-primary">⚡</span>
            <span className="text-lg font-semibold text-foreground">FoundrAI</span>
          </a>
          <button onClick={toggleSidebar} className="md:hidden text-muted hover:text-foreground">
            <X size={18} />
          </button>
        </div>

        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {navItems.map(({ to, label, icon: Icon }) => (
            <a
              key={to}
              href={to}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors',
                location.pathname === to
                  ? 'bg-primary/10 text-primary font-medium'
                  : 'text-muted hover:text-foreground hover:bg-border/50'
              )}
            >
              <Icon size={18} />
              {label}
            </a>
          ))}

          {data && data.projects.length > 0 && (
            <div className="mt-6">
              <p className="px-3 text-xs font-semibold text-muted uppercase tracking-wider mb-2">Projects</p>
              {data.projects.map((p) => (
                <a
                  key={p.project_id}
                  href={`/projects/${p.project_id}`}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors',
                    location.pathname.includes(p.project_id)
                      ? 'bg-primary/10 text-primary font-medium'
                      : 'text-muted hover:text-foreground hover:bg-border/50'
                  )}
                >
                  <FolderKanban size={16} />
                  <span className="truncate">{p.name}</span>
                </a>
              ))}
            </div>
          )}
        </nav>

        <div className="p-4 border-t border-border text-xs text-muted">
          FoundrAI v0.2.0
        </div>
      </aside>
    </>
  );
}
