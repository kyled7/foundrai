import { useEffect, useCallback } from 'react';
import { useSprintFeed } from '@/stores/sprint-feed';
import { useSprint } from '@/hooks/use-sprints';
import { useTasks } from '@/hooks/use-tasks';
import { useAgents } from '@/hooks/use-agents';
import { useApprovals, useApprove, useReject, useSprintCost } from '@/hooks/use-analytics';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { ProgressBar } from './ProgressBar';
import { TeamStatus } from './TeamStatus';
import { TaskList } from './TaskList';
import { CostTracker } from './CostTracker';
import { ActivityFeed } from './ActivityFeed';
import { SprintChat } from './SprintChat';
import { ArtifactDrawer } from './ArtifactDrawer';
import { api } from '@/lib/api';
import { Pause, Play, X, Clock } from 'lucide-react';
import { useState } from 'react';

interface CommandCenterProps {
  projectId: string;
  sprintId: string;
}

export function CommandCenter({ projectId, sprintId }: CommandCenterProps) {
  const { events, connect, disconnect, isConnected } = useSprintFeed();
  const { data: sprint } = useSprint(sprintId);
  
  const { data: tasks } = useTasks(sprintId);
  const { data: agentsData } = useAgents(projectId);
  const { data: costData } = useSprintCost(sprintId);
  const { data: approvalsData } = useApprovals(sprintId);
  const approve = useApprove();
  const reject = useReject();
  const [filterAgent, setFilterAgent] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Connect WebSocket
  useEffect(() => {
    connect(sprintId);
    return () => disconnect();
  }, [sprintId, connect, disconnect]);

  // Timer
  useEffect(() => {
    const interval = setInterval(() => setElapsedSeconds(s => s + 1), 1000);
    return () => clearInterval(interval);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      const pendingApproval = approvalsData?.approvals?.find(a => a.status === 'pending');
      if (e.key === 'a' && pendingApproval) {
        approve.mutate({ id: pendingApproval.approval_id });
      } else if (e.key === 'r' && pendingApproval) {
        reject.mutate({ id: pendingApproval.approval_id });
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [approvalsData, approve, reject]);

  const handleApprove = useCallback((id: string) => approve.mutate({ id }), [approve]);
  const handleReject = useCallback((id: string) => reject.mutate({ id }), [reject]);

  const handleSendMessage = useCallback(async (message: string, targetAgent?: string) => {
    try {
      await api.sprints.message(sprintId, message, targetAgent);
    } catch {
      // Backend may not support this yet
    }
  }, [sprintId]);

  const handlePause = async () => {
    try { await api.sprints.pause(sprintId); } catch { /* not available */ }
  };
  const handleResume = async () => {
    try { await api.sprints.resume(sprintId); } catch { /* not available */ }
  };
  const handleCancel = async () => {
    try { await api.sprints.cancel(sprintId); } catch { /* not available */ }
  };

  const formatTime = (s: number) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    return `${h > 0 ? `${h}:` : ''}${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
  };

  const isActive = sprint?.status === 'in_progress' || sprint?.status === 'planning';
  const isPaused = sprint?.status === 'review'; // approximate
  const completedTasks = tasks?.filter(t => t.status === 'completed').length ?? 0;
  const totalTasks = tasks?.length ?? 0;

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)]">
      {/* Top bar */}
      <div className="flex items-center gap-3 px-4 py-2 border-b border-border bg-card shrink-0">
        <div className="flex-1 min-w-0">
          <p className="text-sm text-foreground font-medium truncate">{sprint?.goal ?? 'Sprint'}</p>
        </div>
        {sprint && <StatusBadge status={sprint.status} />}
        <div className="flex items-center gap-1 text-xs text-muted">
          <Clock size={12} />
          {formatTime(elapsedSeconds)}
        </div>
        <div className="flex items-center gap-1 text-xs text-muted">
          {isConnected ? (
            <span className="w-2 h-2 rounded-full bg-green-400" />
          ) : (
            <span className="w-2 h-2 rounded-full bg-red-400" />
          )}
          {isConnected ? 'Live' : 'Disconnected'}
        </div>

        {/* Controls */}
        <div className="flex gap-1">
          {isActive && (
            <button onClick={handlePause} className="p-1.5 text-muted hover:text-yellow-400 rounded-md hover:bg-border/50" title="Pause">
              <Pause size={14} />
            </button>
          )}
          {isPaused && (
            <button onClick={handleResume} className="p-1.5 text-muted hover:text-green-400 rounded-md hover:bg-border/50" title="Resume">
              <Play size={14} />
            </button>
          )}
          <button onClick={handleCancel} className="p-1.5 text-muted hover:text-red-400 rounded-md hover:bg-border/50" title="Cancel">
            <X size={14} />
          </button>
        </div>
      </div>

      {/* Main content: two columns */}
      <div className="flex flex-1 min-h-0">
        {/* Left panel */}
        <div className="w-72 border-r border-border overflow-y-auto p-3 space-y-4 shrink-0 hidden md:block">
          <ProgressBar completed={completedTasks} total={totalTasks} />

          {agentsData?.agents && (
            <TeamStatus
              agents={agentsData.agents}
              selectedAgent={filterAgent}
              onSelectAgent={setFilterAgent}
            />
          )}

          {tasks && tasks.length > 0 && <TaskList tasks={tasks} />}

          <CostTracker
            totalCost={costData?.total_cost_usd ?? 0}
            byAgent={costData?.by_agent as Record<string, { cost_usd: number }> | undefined}
          />

          {approvalsData && approvalsData.pending_count > 0 && (
            <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-2 text-center">
              <p className="text-xs text-yellow-400 font-medium">{approvalsData.pending_count} pending approval(s)</p>
              <p className="text-[10px] text-muted">Press A to approve, R to reject</p>
            </div>
          )}
        </div>

        {/* Right panel: Activity Feed + Chat */}
        <div className="flex-1 flex flex-col min-h-0">
          <ActivityFeed
            events={events}
            filterAgent={filterAgent}
            onApprove={handleApprove}
            onReject={handleReject}
          />
          <SprintChat
            onSend={handleSendMessage}
            agents={agentsData?.agents?.filter(a => a.enabled).map(a => a.agent_role) ?? []}
            disabled={!isActive}
          />
        </div>
      </div>

      {/* Bottom drawer: Artifacts */}
      <ArtifactDrawer artifacts={[]} />
    </div>
  );
}
