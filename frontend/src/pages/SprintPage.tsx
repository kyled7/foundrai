import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { getSprint, listEvents } from '../api/sprints';
import { listApprovals } from '../api/approvals';
import { executeSprint, cancelSprint } from '../api/execution';
import { useSprintStore } from '../stores/sprintStore';
import { useEventStore } from '../stores/eventStore';
import { useApprovalStore } from '../stores/approvalStore';
import { useSprintWebSocket } from '../hooks/useSprintWebSocket';
import { SprintBoard } from '../components/sprint/SprintBoard';
import { AgentFeed } from '../components/feed/AgentFeed';
import { GoalTree } from '../components/tree/GoalTree';
import { ApprovalBanner } from '../components/approvals/ApprovalBanner';
import { ApprovalQueue } from '../components/approvals/ApprovalQueue';
import { TeamPanel } from '../components/team/TeamPanel';
import { RetrospectiveView } from '../components/retrospective/RetrospectiveView';
import type { WSMessage, TaskResponse, ApprovalRequest as ApprovalRequestType } from '../types';
import { cn } from '../utils/cn';

type Tab = 'board' | 'feed' | 'tree' | 'approvals' | 'team' | 'retro';

export function SprintPage() {
  const { sprintId } = useParams<{ sprintId: string }>();
  const [activeTab, setActiveTab] = useState<Tab>('board');
  const [executing, setExecuting] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const sprint = useSprintStore((s) => s.sprint);
  const setSprint = useSprintStore((s) => s.setSprint);
  const setLoading = useSprintStore((s) => s.setLoading);
  const updateTaskStatus = useSprintStore((s) => s.updateTaskStatus);
  const addTask = useSprintStore((s) => s.addTask);
  const addEvent = useEventStore((s) => s.addEvent);
  const clearEvents = useEventStore((s) => s.clearEvents);
  const setApprovals = useApprovalStore((s) => s.setApprovals);
  const addApproval = useApprovalStore((s) => s.addApproval);
  const resolveApproval = useApprovalStore((s) => s.resolveApproval);

  const loadSprint = useCallback(() => {
    if (!sprintId) return;
    getSprint(sprintId).then((data) => {
      setSprint(data);
      setLoading(false);
    }).catch(() => {
      setLoading(false);
    });
  }, [sprintId, setSprint, setLoading]);

  // Load sprint data
  useEffect(() => {
    if (!sprintId) return;
    setLoading(true);
    clearEvents();
    loadSprint();

    // Load historical events from API
    listEvents(sprintId).then((data) => {
      for (const evt of data.events) {
        addEvent({
          type: evt.event_type,
          data: evt.data,
          timestamp: evt.timestamp,
          sequence: evt.event_id,
        });
      }
    }).catch(() => {});

    listApprovals(sprintId).then((data) => {
      setApprovals(data.approvals);
    }).catch(() => {});
  }, [sprintId, setSprint, setLoading, clearEvents, setApprovals]);

  // Handle WebSocket events
  const handleEvent = useCallback((event: WSMessage) => {
    addEvent(event);

    const d = event.data as Record<string, unknown>;
    switch (event.type) {
      case 'task.status_changed':
        updateTaskStatus(d.task_id as string, d.status as TaskResponse['status']);
        break;
      case 'task.created':
        addTask(d.task as TaskResponse);
        break;
      case 'approval.requested':
        addApproval(d.approval as ApprovalRequestType);
        break;
      case 'approval.resolved':
        resolveApproval(d.approval_id as string, d.status as ApprovalRequestType['status']);
        break;
      case 'sprint.status_changed':
        // Reload sprint data on status change to get updated metrics/tasks
        loadSprint();
        break;
    }
  }, [addEvent, updateTaskStatus, addTask, addApproval, resolveApproval, loadSprint]);

  useSprintWebSocket({
    sprintId: sprintId ?? '',
    onEvent: handleEvent,
    enabled: !!sprintId,
  });

  const handleExecute = async () => {
    if (!sprintId) return;
    setExecuting(true);
    try {
      await executeSprint(sprintId);
      loadSprint();
    } catch {
      // Could show error toast
    } finally {
      setExecuting(false);
    }
  };

  const handleCancel = async () => {
    if (!sprintId) return;
    setCancelling(true);
    try {
      await cancelSprint(sprintId);
      loadSprint();
    } catch {
      // Could show error toast
    } finally {
      setCancelling(false);
    }
  };

  if (!sprintId) return <div className="p-6">No sprint selected</div>;

  const isCreated = sprint?.status === 'created';
  const isFailed = sprint?.status === 'failed';
  const isRunning = sprint?.status === 'planning' || sprint?.status === 'executing' || sprint?.status === 'reviewing';

  const tabs: { key: Tab; label: string }[] = [
    { key: 'board', label: 'Board' },
    { key: 'feed', label: 'Feed' },
    { key: 'tree', label: 'Tree' },
    { key: 'approvals', label: 'Approvals' },
    { key: 'team', label: 'Team' },
    { key: 'retro', label: 'Retro' },
  ];

  return (
    <div className="flex flex-col h-full">
      <ApprovalBanner onReview={() => setActiveTab('approvals')} />

      {/* Sprint header with action buttons */}
      {sprint && (isCreated || isFailed || isRunning) && (
        <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div className="text-sm">
            <span className="font-medium">Sprint #{sprint.sprint_number}</span>
            <span className="text-gray-500 ml-2">{sprint.goal}</span>
          </div>
          <div className="flex gap-2">
            {(isCreated || isFailed) && (
              <button
                onClick={handleExecute}
                disabled={executing}
                className="px-4 py-1.5 text-sm rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
              >
                {executing ? 'Starting...' : isFailed ? 'Retry Sprint' : 'Execute Sprint'}
              </button>
            )}
            {isRunning && (
              <button
                onClick={handleCancel}
                disabled={cancelling}
                className="px-4 py-1.5 text-sm rounded bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
              >
                {cancelling ? 'Cancelling...' : 'Cancel'}
              </button>
            )}
          </div>
        </div>
      )}

      <div className="flex border-b border-gray-200 dark:border-gray-700 px-4">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={cn(
              'px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors',
              activeTab === tab.key
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-hidden">
        {activeTab === 'board' && <SprintBoard />}
        {activeTab === 'feed' && <AgentFeed />}
        {activeTab === 'tree' && <GoalTree sprintId={sprintId} />}
        {activeTab === 'approvals' && <ApprovalQueue />}
        {activeTab === 'team' && sprint && <TeamPanel projectId={sprint.project_id} />}
        {activeTab === 'retro' && <RetrospectiveView sprintId={sprintId} />}
      </div>
    </div>
  );
}
