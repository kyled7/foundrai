import { ErrorBoundary } from './ErrorBoundary';

interface RouteErrorBoundaryProps {
  children: React.ReactNode;
}

export function RouteErrorBoundary({ children }: RouteErrorBoundaryProps) {
  return <ErrorBoundary>{children}</ErrorBoundary>;
}
