import { useState } from 'react';
import { useLearnings, useSearchLearnings, usePinLearning, useUpdateLearning, useDeleteLearning } from '@/hooks/use-analytics';
import { useSprints } from '@/hooks/use-sprints';
import { SearchBar } from './SearchBar';
import { FilterPanel, type FilterState } from './FilterPanel';
import { LearningCard } from './LearningCard';
import { PageSkeleton } from '@/components/shared/LoadingSkeleton';
import type { Learning } from '@/lib/types';
import { Brain, AlertCircle } from 'lucide-react';

interface KnowledgeBasePageProps {
  projectId: string;
}

export function KnowledgeBasePage({ projectId }: KnowledgeBasePageProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<FilterState>({
    category: null,
    sprintId: null,
    dateRange: null,
  });

  const learningsQuery = useLearnings(projectId);
  const searchQuery_enabled = searchQuery.trim().length > 0;
  const searchResults = useSearchLearnings(projectId, searchQuery);
  const sprintsQuery = useSprints(projectId);

  const pinMutation = usePinLearning();
  const updateMutation = useUpdateLearning();
  const deleteMutation = useDeleteLearning();

  const isLoading = learningsQuery.isLoading || sprintsQuery.isLoading;

  if (isLoading) return <PageSkeleton />;

  // Use search results if searching, otherwise use all learnings
  const allLearnings = searchQuery_enabled && searchResults.data
    ? searchResults.data.learnings
    : learningsQuery.data?.learnings ?? [];

  // Filter learnings
  let filteredLearnings = allLearnings;

  if (filters.category) {
    filteredLearnings = filteredLearnings.filter(l => l.category === filters.category);
  }

  if (filters.sprintId) {
    filteredLearnings = filteredLearnings.filter(l => l.sprint_id === filters.sprintId);
  }

  if (filters.dateRange) {
    filteredLearnings = filteredLearnings.filter(l => {
      const date = l.created_at.slice(0, 10);
      return date >= filters.dateRange!.from && date <= filters.dateRange!.to;
    });
  }

  // Separate pinned and unpinned
  const pinnedLearnings = filteredLearnings.filter(l => l.pinned);
  const unpinnedLearnings = filteredLearnings.filter(l => !l.pinned);

  // Get sprints for filter
  const sprints = sprintsQuery.data ?? [];
  const availableSprints = sprints.map(s => ({
    sprint_id: s.sprint_id,
    sprint_number: s.sprint_number,
  }));

  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  const handlePin = (learning: Learning) => {
    pinMutation.mutate({
      projectId,
      learningId: learning.learning_id,
      pinned: !learning.pinned
    });
  };

  const handleEdit = (learning: Learning) => {
    // TODO: Implement edit modal
    const newContent = prompt('Edit learning:', learning.content);
    if (newContent && newContent !== learning.content) {
      updateMutation.mutate({
        projectId,
        learningId: learning.learning_id,
        data: { content: newContent },
      });
    }
  };

  const handleDelete = (learning: Learning) => {
    if (confirm('Are you sure you want to delete this learning?')) {
      deleteMutation.mutate({ projectId, learningId: learning.learning_id });
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-3">
        <Brain size={28} className="text-primary" />
        <h1 className="text-2xl font-bold text-foreground">Knowledge Base</h1>
      </div>

      {/* Search Bar */}
      <SearchBar
        onSearch={handleSearch}
        placeholder="Ask a question about past sprints..."
        loading={searchResults.isLoading}
      />

      {/* Filter Panel */}
      <FilterPanel
        value={filters}
        onChange={setFilters}
        availableSprints={availableSprints}
      />

      {/* Results */}
      <div className="space-y-6">
        {/* Pinned Learnings */}
        {pinnedLearnings.length > 0 && (
          <div className="space-y-3">
            <h2 className="text-sm font-semibold text-muted uppercase tracking-wide">
              Pinned ({pinnedLearnings.length})
            </h2>
            <div className="space-y-2">
              {pinnedLearnings.map(learning => (
                <LearningCard
                  key={learning.learning_id}
                  learning={learning}
                  onPin={handlePin}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          </div>
        )}

        {/* Unpinned Learnings */}
        {unpinnedLearnings.length > 0 && (
          <div className="space-y-3">
            <h2 className="text-sm font-semibold text-muted uppercase tracking-wide">
              All Learnings ({unpinnedLearnings.length})
            </h2>
            <div className="space-y-2">
              {unpinnedLearnings.map(learning => (
                <LearningCard
                  key={learning.learning_id}
                  learning={learning}
                  onPin={handlePin}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {filteredLearnings.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
            <AlertCircle size={48} className="text-muted mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              {searchQuery_enabled ? 'No results found' : 'No learnings yet'}
            </h3>
            <p className="text-sm text-muted max-w-md">
              {searchQuery_enabled
                ? 'Try adjusting your search query or filters.'
                : 'Learnings from sprint retrospectives will appear here.'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
