import { useEffect, useState, useCallback } from 'react';
import { useParams } from '@tanstack/react-router';
import { useSprint, useStartSprint, useCancelSprint } from '@/hooks/use-sprints';
import { useSprintStore } from '@/stores/sprintStore';
import { useEventStore } from '@/stores/eventStore';
import { useApprovalStore } from '@/stores/approvalStore';
import { useSprintWebSocket } from '@/hooks/useSprintWebSocket';
import { api } from '@/lib/api';
import { SprintBoard } from '@/components/sprint/SprintBoard';
import { AgentFeed } from '@/components/feed/AgentFeed';
import { GoalTree } from '@/components/tree/GoalTree';
import { ApprovalBanner } from '@/components/approvals/ApprovalBanner';
import { ApprovalQueue } from '@/components/approvals/ApprovalQueue';
import { TeamPanel } from '@/components/team/TeamPanel';
import { RetrospectiveView } from '@/components/retrospective/RetrospectiveView';
import { PageSkeleton } from '@/components/shared/PageSkeleton';
import type { WSMessage, TaskResponse, ApprovalRequest as ApprovalRequestType } from '@/lib/types';
import { cn } from '@/lib/utils';

const tabs = ['board', 'feed', 'tree', 'approvals', 'team', 'retro'] as const;
type Tab = typeof tabs[number];

export function SprintDetailPage() {
  const { sprintId, projectId } = useParams({ strict: false }) as { sprintId: string; projectId: string };
  const [activeTab, setActiveTab] = useState<Tab>('board');
  const { data: sprint, isLoading, refetch } = useSprint(sprintId);
  const startSprint = useStartSprint();
  const cancelSprint = useCancelSprint();

  const setSprint = useSprintStore((s) => s.setSprint);
  const setLoading = useSprintStore((s) => s.setLoading);
  const updateTaskStatus = useSprintStore((s) => s.updateTaskStatus);
  const addTask = useSprintStore((s) => s.addTask);
  const addEvent = useEventStore((s) => s.addEvent);
  const clearEvents = useEventStore((s) => s.clearEvents);
  const setApprovals = useApprovalStore((s) => s.setApprovals);
  const addApproval = useApprovalStore((s) => s.addApproval);
  const resolveApproval = useApprovalStore((s) => s.resolveApproval);

  // Load sprint data and sync with store
  useEffect(() => {
    if (!sprintId) return;
    setLoading(true);
    clearEvents();

    // Load historical events from API
    api.events.list(sprintId).then((data) => {
      for (const evt of data.events) {
        addEvent({
          type: evt.event_type as WSMessage['type'],
          data: evt.data,
          timestamp: evt.timestamp,
          sequence: evt.event_id,
        });
      }
    }).catch(() => {});

    // Load approvals
    api.approvals.list(sprintId).then((data) => {
      setApprovals(data.approvals);
    }).catch(() => {});
  }, [sprintId, setLoading, clearEvents, addEvent, setApprovals]);

  // Sync sprint data to store when loaded
  useEffect(() => {
    if (sprint) {
      // Load tasks for the sprint
      api.tasks.list(sprintId).then((tasks) => {
        // Construct SprintResponse with tasks
        const sprintResponse = {
          ...sprint,
          tasks,
          metrics: undefined,
          error: null,
        };
        setSprint(sprintResponse);
        setLoading(false);
      }).catch(() => {
        // If tasks fail to load, still set the sprint with empty tasks
        setSprint({
          ...sprint,
          tasks: [],
          metrics: undefined,
          error: null,
        });
        setLoading(false);
      });
    }
  }, [sprint, sprintId, setSprint, setLoading]);

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
        refetch();
        break;
    }
  }, [addEvent, updateTaskStatus, addTask, addApproval, resolveApproval, refetch]);

  useSprintWebSocket({
    sprintId: sprintId ?? '',
    onEvent: handleEvent,
    enabled: !!sprintId,
  });

  const handleExecute = async () => {
    if (!sprintId) return;
    await startSprint.mutateAsync(sprintId);
  };

  const handleCancel = async () => {
    if (!sprintId) return;
    await cancelSprint.mutateAsync(sprintId);
  };

  if (isLoading || !sprint) return <PageSkeleton layout="detail" />;

  const isCreated = sprint.status === 'created';
  const isFailed = sprint.status === 'failed';
  const isRunning = sprint.status === 'planning' || sprint.status === 'in_progress' || sprint.status === 'review';

  const tabsList: { key: Tab; label: string }[] = [
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
      {(isCreated || isFailed || isRunning) && (
        <div className="px-4 py-3 bg-muted/50 border-b border-border flex items-center justify-between">
          <div className="text-sm">
            <span className="font-medium text-foreground">Sprint #{sprint.sprint_number}</span>
            <span className="text-muted ml-2">{sprint.goal}</span>
          </div>
          <div className="flex gap-2">
            {(isCreated || isFailed) && (
              <button
                onClick={handleExecute}
                disabled={startSprint.isPending}
                className="px-4 py-1.5 text-sm rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
              >
                {startSprint.isPending ? 'Starting...' : isFailed ? 'Retry Sprint' : 'Execute Sprint'}
              </button>
            )}
            {isRunning && (
              <button
                onClick={handleCancel}
                disabled={cancelSprint.isPending}
                className="px-4 py-1.5 text-sm rounded bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
              >
                {cancelSprint.isPending ? 'Cancelling...' : 'Cancel'}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-border px-4">
        {tabsList.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={cn(
              'px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors',
              activeTab === tab.key
                ? 'border-primary text-primary'
                : 'border-transparent text-muted hover:text-foreground'
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'board' && <SprintBoard />}
        {activeTab === 'feed' && <AgentFeed />}
        {activeTab === 'tree' && <GoalTree sprintId={sprintId} />}
        {activeTab === 'approvals' && <ApprovalQueue />}
        {activeTab === 'team' && <TeamPanel projectId={projectId} />}
        {activeTab === 'retro' && <RetrospectiveView sprintId={sprintId} />}
      </div>
    </div>
  );
}
