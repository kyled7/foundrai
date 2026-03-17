import { Outlet } from '@tanstack/react-router';
import { Toaster } from 'sonner';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { SkipToContent } from '@/components/shared/SkipToContent';
import { RouteErrorBoundary } from '@/components/shared/RouteErrorBoundary';
import { useUI } from '@/stores/ui';

export function AppShell() {
  const theme = useUI((s) => s.theme);
  const resolvedTheme = theme === 'system'
    ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
    : theme;

  return (
    <div className="flex h-screen bg-background">
      <SkipToContent />
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main id="main-content" className="flex-1 overflow-y-auto">
          <RouteErrorBoundary>
            <Outlet />
          </RouteErrorBoundary>
        </main>
      </div>
      <Toaster position="bottom-right" theme={resolvedTheme} richColors closeButton />
    </div>
  );
}
