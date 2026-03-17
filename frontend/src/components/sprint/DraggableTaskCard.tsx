import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { TaskResponse } from '../../types';
import { TaskCard } from './TaskCard';
import { cn } from '../../utils/cn';

interface Props {
  task: TaskResponse;
}

export function DraggableTaskCard({ task }: Props) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: task.task_id,
    data: {
      type: 'task',
      task,
    },
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'cursor-grab active:cursor-grabbing',
        isDragging && 'opacity-50 z-50'
      )}
      {...attributes}
      {...listeners}
    >
      <TaskCard task={task} />
    </div>
  );
}
