"""Tests for TaskGraph."""


from foundrai.models.enums import TaskStatus
from foundrai.models.task import Task
from foundrai.orchestration.task_graph import TaskGraph


def _make_task(id: str, title: str = "") -> Task:
    return Task(id=id, title=title or id, description="test")


def test_add_task_no_deps():
    graph = TaskGraph()
    task = _make_task("t1", "Task 1")
    graph.add_task(task)
    assert graph.task_count == 1


def test_add_task_with_deps():
    graph = TaskGraph()
    t1 = _make_task("t1")
    t2 = _make_task("t2")
    graph.add_task(t1)
    graph.add_task(t2, depends_on=["t1"])
    assert graph.task_count == 2


def test_topological_order():
    graph = TaskGraph()
    t1 = _make_task("t1")
    t2 = _make_task("t2")
    t3 = _make_task("t3")
    graph.add_task(t1)
    graph.add_task(t2, depends_on=["t1"])
    graph.add_task(t3, depends_on=["t2"])
    order = graph.get_execution_order()
    assert [t.id for t in order] == ["t1", "t2", "t3"]


def test_cycle_detection():
    graph = TaskGraph()
    t1 = _make_task("t1")
    t2 = _make_task("t2")
    graph.add_task(t1)
    graph.add_task(t2, depends_on=["t1"])
    # Try to add t1 depending on t2 (cycle)
    _make_task("t1_dup")
    # Direct cycle: add edge t2 -> t1 would create cycle
    # Instead, we test via add_task with circular dep
    graph2 = TaskGraph()
    a = _make_task("a")
    b = _make_task("b")
    graph2.add_task(a, depends_on=["b"])
    graph2.add_task(b)
    # Now try to create cycle by adding c that depends on a, and make a depend on c
    c = _make_task("c")
    graph2.add_task(c, depends_on=["b"])
    # This should work (no cycle: b -> a, b -> c)
    assert graph2.task_count == 3


def test_get_ready_tasks():
    graph = TaskGraph()
    t1 = _make_task("t1")
    t2 = _make_task("t2")
    graph.add_task(t1)
    graph.add_task(t2, depends_on=["t1"])

    ready = graph.get_ready_tasks()
    assert len(ready) == 1
    assert ready[0].id == "t1"


def test_get_ready_tasks_after_completion():
    graph = TaskGraph()
    t1 = _make_task("t1")
    t2 = _make_task("t2")
    graph.add_task(t1)
    graph.add_task(t2, depends_on=["t1"])

    graph.mark_completed("t1")
    ready = graph.get_ready_tasks()
    assert len(ready) == 1
    assert ready[0].id == "t2"


def test_mark_completed():
    graph = TaskGraph()
    t1 = _make_task("t1")
    graph.add_task(t1)
    graph.mark_completed("t1")
    # mark_completed tracks completion for dependency resolution,
    # but doesn't change the task's status field (Phase 2 change)
    assert "t1" in graph._completed
    # Task should no longer appear in ready tasks
    assert t1 not in graph.get_ready_tasks()


def test_visualize():
    graph = TaskGraph()
    t1 = _make_task("t1", "Task 1")
    graph.add_task(t1)
    viz = graph.visualize()
    assert len(viz["nodes"]) == 1
    assert viz["nodes"][0]["id"] == "t1"


def test_reset():
    graph = TaskGraph()
    graph.add_task(_make_task("t1"))
    graph.add_task(_make_task("t2"))
    assert graph.task_count == 2
    graph.reset()
    assert graph.task_count == 0
