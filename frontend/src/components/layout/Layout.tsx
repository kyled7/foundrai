import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { ErrorBoundary } from '../shared/ErrorBoundary';
import { ToastContainer } from '../shared/Toast';

export function Layout() {
  return (
    <div className="h-screen flex bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded"
      >
        Skip to main content
      </a>
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <div id="main-content" className="flex-1 overflow-hidden">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </div>
      </main>
      <ToastContainer />
    </div>
  );
}
