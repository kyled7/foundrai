import { DndContext, DragEndEvent, PointerSensor, useSensor, useSensors, DragOverlay } from '@dnd-kit/core';
import { useState } from 'react';
import { useSprintStore } from '../../stores/sprintStore';
import { KanbanColumn } from './KanbanColumn';
import { TaskCard } from './TaskCard';
import type { TaskStatus, TaskResponse } from '../../types';

const COLUMNS: { key: string; title: string; statuses: TaskStatus[]; color: string }[] = [
  { key: 'backlog',     title: 'Backlog',     statuses: ['backlog', 'blocked'], color: 'gray' },
  { key: 'in_progress', title: 'In Progress', statuses: ['in_progress'],        color: 'blue' },
  { key: 'in_review',   title: 'In Review',   statuses: ['in_review'],          color: 'yellow' },
  { key: 'done',        title: 'Done',        statuses: ['done'],               color: 'green' },
  { key: 'failed',      title: 'Failed',      statuses: ['failed'],             color: 'red' },
];

function BoardSkeleton() {
  return (
    <div className="flex gap-4 overflow-x-auto p-4 h-full" role="region" aria-label="Loading sprint board">
      {COLUMNS.map((col) => (
        <div
          key={col.key}
          className="flex-shrink-0 w-80 bg-gray-50 dark:bg-gray-800 rounded-lg p-4"
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

export function SprintBoard() {
  const tasks = useSprintStore((s) => s.tasks);
  const loading = useSprintStore((s) => s.loading);
  const updateTaskStatus = useSprintStore((s) => s.updateTaskStatus);
  const [activeTask, setActiveTask] = useState<TaskResponse | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  );

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

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <div className="flex gap-4 overflow-x-auto p-4 h-full" role="region" aria-label="Sprint task board">
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
  );
}
