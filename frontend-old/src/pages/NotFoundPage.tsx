import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-50 dark:bg-gray-950">
      <p className="text-6xl mb-4">🔍</p>
      <h1 className="text-2xl font-bold mb-2">Page Not Found</h1>
      <p className="text-gray-500 mb-4">The page you're looking for doesn't exist.</p>
      <Link to="/" className="text-blue-600 hover:underline">Go to Dashboard</Link>
    </div>
  );
}
