import { useState } from 'react';
import { Search, X, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
  loading?: boolean;
}

export function SearchBar({
  onSearch,
  placeholder = 'Ask a question about past sprints...',
  className,
  disabled = false,
  loading = false,
}: SearchBarProps) {
  const [query, setQuery] = useState('');

  const handleSearch = () => {
    if (!query.trim() || disabled || loading) return;
    onSearch(query.trim());
  };

  const handleClear = () => {
    setQuery('');
    onSearch('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    } else if (e.key === 'Escape') {
      handleClear();
    }
  };

  return (
    <div
      className={cn(
        'flex items-center gap-2 bg-background border border-border rounded-lg px-4 py-3 transition-colors',
        'focus-within:border-primary focus-within:ring-1 focus-within:ring-primary',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
    >
      <Search size={18} className="text-muted shrink-0" />
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled || loading}
        aria-label="Search knowledge base"
        className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted outline-none disabled:cursor-not-allowed"
      />
      {loading && (
        <Loader2 size={16} className="text-muted animate-spin shrink-0" />
      )}
      {!loading && query && (
        <button
          onClick={handleClear}
          disabled={disabled}
          aria-label="Clear search"
          className="p-1 text-muted hover:text-foreground transition-colors rounded disabled:cursor-not-allowed"
        >
          <X size={16} />
        </button>
      )}
      <button
        onClick={handleSearch}
        disabled={!query.trim() || disabled || loading}
        className={cn(
          'px-4 py-1.5 bg-primary text-primary-foreground text-sm font-medium rounded-md transition-opacity',
          'hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed shrink-0'
        )}
      >
        Search
      </button>
    </div>
  );
}
