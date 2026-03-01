import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { getSprint, listEvents } from '../api/sprints';
import { listApprovals } from '../api/approvals';
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

  // Load sprint data
  useEffect(() => {
    if (!sprintId) return;
    setLoading(true);
    clearEvents();

    getSprint(sprintId).then((data) => {
      setSprint(data);
    }).catch(() => {
      setLoading(false);
    });

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
    }
  }, [addEvent, updateTaskStatus, addTask, addApproval, resolveApproval]);

  useSprintWebSocket({
    sprintId: sprintId ?? '',
    onEvent: handleEvent,
    enabled: !!sprintId,
  });

  if (!sprintId) return <div className="p-6">No sprint selected</div>;

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
