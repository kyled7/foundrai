import { useQuery } from '@tanstack/react-query';
import { DndContext, PointerSensor, useSensor, useSensors, DragOverlay } from '@dnd-kit/core';
import type { DragEndEvent } from '@dnd-kit/core';
import { useState } from 'react';
import { useSprintStore } from '@/stores/sprintStore';
import { useTraceStore } from '@/stores/traceStore';
import { ErrorBoundary } from '../shared/ErrorBoundary';
import { KanbanColumn } from './KanbanColumn';
import { BudgetWarning } from './BudgetWarning';
import { DecisionTracePanel } from '../traces/DecisionTracePanel';
import { CommunicationGraph } from '../graph/CommunicationGraph';
import { api } from '@/lib/api';
import type { TaskStatus, Task } from '@/lib/types';
import { TaskCard } from './TaskCard';
import { getTaskTraces } from '@/api/traces';
import { X, LayoutDashboard, Network } from 'lucide-react';
import { cn } from '@/lib/utils';

const COLUMNS: { key: string; title: string; statuses: TaskStatus[]; color: string }[] = [
  { key: 'backlog',     title: 'Backlog',     statuses: ['pending', 'blocked'], color: 'gray' },
  { key: 'in_progress', title: 'In Progress', statuses: ['in_progress'],        color: 'blue' },
  { key: 'completed',   title: 'Completed',   statuses: ['completed'],          color: 'green' },
  { key: 'failed',      title: 'Failed',      statuses: ['failed'],             color: 'red' },
];

type ViewTab = 'board' | 'graph';

const tabs: { id: ViewTab; label: string; icon: typeof LayoutDashboard }[] = [
  { id: 'board', label: 'Board', icon: LayoutDashboard },
  { id: 'graph', label: 'Communication Graph', icon: Network },
];

interface SprintBoardProps {
  sprintId?: string;
}

function BoardSkeleton() {
  return (
    <div className="flex gap-2 md:gap-3 xl:gap-4 overflow-x-auto p-2 md:p-3 xl:p-4 h-full" role="region" aria-label="Loading sprint board">
      {COLUMNS.map((col) => (
        <div
          key={col.key}
          className="flex-shrink-0 w-60 md:w-72 xl:w-80 bg-gray-50 dark:bg-gray-800 rounded-lg p-4"
        >
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-4 animate-pulse" />
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div
                key={i}
                className="h-32 bg-white dark:bg-gray-900 rounded-lg shadow animate-pulse"
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function SprintBoardContent({ sprintId }: SprintBoardProps) {
  const tasks = useSprintStore((s) => s.tasks);
  const loading = useSprintStore((s) => s.loading);
  const error = useSprintStore((s) => s.error);
  const updateTaskStatus = useSprintStore((s) => s.updateTaskStatus);
  const clear = useSprintStore((s) => s.clear);
  const setTraces = useTraceStore((s) => s.setTraces);
  const clearTraces = useTraceStore((s) => s.clearTraces);

  // Fetch budget status for warning banner (must be before any conditional returns)
  const { data: budgetStatus } = useQuery({
    queryKey: ['sprint', sprintId, 'budget'],
    queryFn: () => api.analytics.budget(sprintId!),
    enabled: !!sprintId,
    refetchInterval: 10000,
  });

  const [activeTab, setActiveTab] = useState<ViewTab>('board');
  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [tracePanelOpen, setTracePanelOpen] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  );

  async function handleTaskClick(taskId: string) {
    setSelectedTaskId(taskId);
    setTracePanelOpen(true);

    try {
      // Fetch traces for the selected task
      const response = await getTaskTraces(taskId);
      setTraces(response.traces);
    } catch (error) {
      // Error fetching traces - user can still see the panel, just no traces
      setTraces([]);
    }
  }

  function handleCloseTracePanel() {
    setTracePanelOpen(false);
    setSelectedTaskId(null);
    clearTraces();
  }

  function handleDragStart(event: { active: { id: string } }) {
    const task = tasks.find((t) => t.task_id === event.active.id);
    setActiveTask(task || null);
  }

  async function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    setActiveTask(null);

    if (!over) return;

    const taskId = active.id as string;
    const targetColumnKey = over.id as string;

    // Find the target column's primary status (first status in the array)
    const targetColumn = COLUMNS.find((col) => col.key === targetColumnKey);
    if (!targetColumn) return;

    const newStatus = targetColumn.statuses[0];

    try {
      // Update task status in store and persist to backend
      await updateTaskStatus(taskId, newStatus);
    } catch (error) {
      // Error is already handled in the store (optimistic update reverted)
      // TODO: Show user-facing error notification
    }
  }

  function handleDragCancel() {
    setActiveTask(null);
  }

  if (loading) {
    return <BoardSkeleton />;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center">
        <div className="text-red-500 text-lg font-semibold mb-2">Failed to load sprint board</div>
        <p className="text-gray-500 dark:text-gray-400 text-sm mb-4">{error}</p>
        <button
          onClick={() => {
            clear();
            window.location.reload();
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    const currentIndex = tabs.findIndex((t) => t.id === activeTab);
    if (e.key === 'ArrowRight') {
      e.preventDefault();
      const next = tabs[(currentIndex + 1) % tabs.length];
      setActiveTab(next.id);
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      const prev = tabs[(currentIndex - 1 + tabs.length) % tabs.length];
      setActiveTab(prev.id);
    }
  }

  return (
    <div className="flex flex-col h-full" role="region" aria-label="Sprint task board">
      {/* Budget warning banner */}
      {sprintId && budgetStatus && (budgetStatus.is_warning || budgetStatus.is_exceeded) && (
        <div className="px-4 pt-4">
          <BudgetWarning budgetStatus={budgetStatus} sprintId={sprintId} />
        </div>
      )}

      {/* Tab Navigation */}
      <div
        role="tablist"
        aria-label="Sprint views"
        className="flex gap-1 border-b border-border overflow-x-auto px-4"
        onKeyDown={handleKeyDown}
      >
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            role="tab"
            aria-selected={activeTab === id}
            aria-controls={`panel-${id}`}
            tabIndex={activeTab === id ? 0 : -1}
            onClick={() => setActiveTab(id)}
            className={cn(
              'flex items-center gap-2 px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors border-b-2 -mb-px',
              activeTab === id
                ? 'border-primary text-primary'
                : 'border-transparent text-muted hover:text-foreground hover:border-border'
            )}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {/* Board View */}
      {activeTab === 'board' && (
        <DndContext
          sensors={sensors}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
          onDragCancel={handleDragCancel}
        >
          <div className="flex gap-2 md:gap-3 xl:gap-4 overflow-x-auto p-2 md:p-3 xl:p-4 flex-1">
            {COLUMNS.map((col) => {
              const filtered = tasks.filter((t) => col.statuses.includes(t.status));
              return (
                <KanbanColumn
                  key={col.key}
                  columnId={col.key}
                  title={col.title}
                  color={col.color}
                  tasks={filtered}
                  count={filtered.length}
                  onTaskClick={handleTaskClick}
                />
              );
            })}
          </div>
          <DragOverlay>
            {activeTask ? (
              <div className="opacity-80 rotate-2">
                <TaskCard task={activeTask} isDragging />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      )}

      {/* Communication Graph View */}
      {activeTab === 'graph' && sprintId && (
        <div className="flex-1 overflow-hidden">
          <CommunicationGraph sprintId={sprintId} />
        </div>
      )}

      {/* Decision Trace Panel Overlay */}
      {tracePanelOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
          onClick={handleCloseTracePanel}
        >
          <div
            className="bg-background rounded-lg shadow-xl w-full max-w-6xl h-[90vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header with close button */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
              <h2 className="text-lg font-semibold">
                Decision Traces {selectedTaskId && `- Task ${selectedTaskId}`}
              </h2>
              <button
                onClick={handleCloseTracePanel}
                className="p-1 hover:bg-accent rounded-md transition-colors"
                aria-label="Close trace panel"
              >
                <X size={20} />
              </button>
            </div>

            {/* Trace Panel Content */}
            <div className="flex-1 overflow-hidden">
              <DecisionTracePanel />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function SprintBoard({ sprintId }: SprintBoardProps = {}) {
  return (
    <ErrorBoundary>
      <SprintBoardContent sprintId={sprintId} />
    </ErrorBoundary>
  );
}
