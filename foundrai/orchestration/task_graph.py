"""TaskGraph — DAG of tasks with dependency tracking."""

from __future__ import annotations

import asyncio

import networkx as nx

from foundrai.models.enums import TaskStatus
from foundrai.models.task import Task


class TaskGraph:
    """DAG of tasks with dependency tracking using NetworkX."""

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()
        self._tasks: dict[str, Task] = {}
        self._completed: set[str] = set()
        self._lock: asyncio.Lock = asyncio.Lock()

    async def add_task(self, task: Task, depends_on: list[str] | None = None) -> None:
        """Add a task to the graph."""
        async with self._lock:
            self._graph.add_node(task.id)
            self._tasks[task.id] = task

            for dep_id in depends_on or []:
                if dep_id in self._graph:
                    self._graph.add_edge(dep_id, task.id)

            if not nx.is_directed_acyclic_graph(self._graph):
                self._graph.remove_node(task.id)
                del self._tasks[task.id]
                raise ValueError(f"Adding task {task.id} would create a cycle")

    async def get_ready_tasks(self) -> list[Task]:
        """Return tasks whose dependencies are all completed."""
        async with self._lock:
            ready = []
            for task_id in self._graph.nodes:
                if task_id in self._completed:
                    continue
                task = self._tasks[task_id]
                if task.status not in (TaskStatus.BACKLOG, "backlog"):
                    continue
                predecessors = list(self._graph.predecessors(task_id))
                if all(p in self._completed for p in predecessors):
                    ready.append(task)
            return ready

    async def get_execution_order(self) -> list[Task]:
        """Return topological sort of all tasks."""
        async with self._lock:
            order = list(nx.topological_sort(self._graph))
            return [self._tasks[tid] for tid in order]

    async def mark_completed(self, task_id: str) -> None:
        """Mark a task as completed in the graph."""
        async with self._lock:
            self._completed.add(task_id)

    async def get_critical_path(self) -> list[Task]:
        """Return the longest path through the DAG."""
        async with self._lock:
            try:
                path = nx.dag_longest_path(self._graph)
                return [self._tasks[tid] for tid in path]
            except nx.NetworkXError:
                return []

    async def visualize(self) -> dict:
        """Return graph data for frontend visualization."""
        async with self._lock:
            nodes = [
                {
                    "id": tid,
                    "data": {
                        "label": t.title,
                        "status": t.status if isinstance(t.status, str) else t.status.value,
                    },
                }
                for tid, t in self._tasks.items()
            ]
            edges = [{"source": u, "target": v} for u, v in self._graph.edges]
            return {"nodes": nodes, "edges": edges}

    async def get_task(self, task_id: str) -> Task:
        """Get a task by ID."""
        async with self._lock:
            return self._tasks[task_id]

    @property
    def task_count(self) -> int:
        """Number of tasks in the graph."""
        return len(self._tasks)

    async def reset(self) -> None:
        """Clear all tasks and edges."""
        async with self._lock:
            self._graph = nx.DiGraph()
            self._tasks = {}
            self._completed = set()
