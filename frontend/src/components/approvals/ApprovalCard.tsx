import { useState, useEffect } from 'react';
import type { ApprovalRequest } from '../../lib/types';
import { approveRequest, rejectRequest } from '../../api/approvals';
import { useApprovalStore } from '../../stores/approvalStore';
import { AgentAvatar } from '../shared/AgentAvatar';
import { ContextRenderer } from './ContextRenderer';
import { Clock } from 'lucide-react';

interface Props {
  approval: ApprovalRequest;
}

export function ApprovalCard({ approval }: Props) {
  const resolveApproval = useApprovalStore((s) => s.resolveApproval);
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState<number>(0);

  // Default timeout: 5 minutes (300 seconds)
  const APPROVAL_TIMEOUT_SECONDS = 300;

  useEffect(() => {
    const createdAt = new Date(approval.created_at).getTime();
    const timeoutMs = APPROVAL_TIMEOUT_SECONDS * 1000;

    const updateTimer = () => {
      const now = Date.now();
      const elapsed = now - createdAt;
      const remaining = Math.max(0, timeoutMs - elapsed);
      setTimeRemaining(Math.floor(remaining / 1000));
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);

    return () => clearInterval(interval);
  }, [approval.created_at]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleDecision = async (approved: boolean) => {
    setLoading(true);
    try {
      if (approved) {
        await approveRequest(approval.approval_id, comment);
        resolveApproval(approval.approval_id, 'approved');
      } else {
        await rejectRequest(approval.approval_id, comment);
        resolveApproval(approval.approval_id, 'rejected');
      }
    } finally {
      setLoading(false);
    }
  };

  if (approval.status !== 'pending') return null;

  return (
    <div className="border-2 border-amber-300 dark:border-amber-700 rounded-lg p-4 bg-amber-50/50 dark:bg-amber-900/10">
      <div className="flex items-start gap-3">
        <AgentAvatar role={approval.agent_id} />
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1">
            <h3 className="font-semibold">{approval.title}</h3>
            <div className="flex items-center gap-1.5 text-xs text-amber-700 dark:text-amber-400">
              <Clock size={12} />
              <span className="font-mono">{formatTime(timeRemaining)}</span>
            </div>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{approval.description}</p>

          <ContextRenderer context={approval.context} actionType={approval.action_type} />

          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Optional feedback for the agent..."
            className="w-full mt-3 text-sm border rounded p-2 h-16 resize-none bg-white dark:bg-gray-800"
          />

          <div className="flex gap-2 mt-3">
            <button
              onClick={() => handleDecision(true)}
              disabled={loading}
              className="px-4 py-1.5 bg-green-600 text-white rounded text-sm font-medium hover:bg-green-700 disabled:opacity-50"
            >
              ✓ Approve
            </button>
            <button
              onClick={() => handleDecision(false)}
              disabled={loading}
              className="px-4 py-1.5 bg-red-600 text-white rounded text-sm font-medium hover:bg-red-700 disabled:opacity-50"
            >
              ✗ Reject
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
