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

export function SprintBoard() {
  const tasks = useSprintStore((s) => s.tasks);
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

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    setActiveTask(null);

    if (!over) return;

    const taskId = active.id as string;
    const targetColumnKey = over.id as string;

    // Find the target column's primary status (first status in the array)
    const targetColumn = COLUMNS.find((col) => col.key === targetColumnKey);
    if (!targetColumn) return;

    const newStatus = targetColumn.statuses[0];

    // Update task status in store
    updateTaskStatus(taskId, newStatus);
  }

  function handleDragCancel() {
    setActiveTask(null);
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
