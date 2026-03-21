import { Outlet } from '@tanstack/react-router';
import { Toaster } from 'sonner';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { SkipToContent } from '@/components/shared/SkipToContent';
import { RouteErrorBoundary } from '@/components/shared/RouteErrorBoundary';
import { WelcomeModal } from '@/components/onboarding/WelcomeModal';
import { useUI } from '@/stores/ui';
import { useOnboarding } from '@/stores/onboarding';

export function AppShell() {
  const theme = useUI((s) => s.theme);
  const isFirstRun = useOnboarding((s) => s.isFirstRun);
  const markFirstRunComplete = useOnboarding((s) => s.markFirstRunComplete);
  const startTutorial = useOnboarding((s) => s.startTutorial);
  const resolvedTheme = theme === 'system'
    ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
    : theme;

  function handleCloseWelcome() {
    markFirstRunComplete();
  }

  function handleStartTutorial() {
    startTutorial();
  }

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
      <WelcomeModal
        open={isFirstRun}
        onClose={handleCloseWelcome}
        onStartTutorial={handleStartTutorial}
      />
    </div>
  );
}
