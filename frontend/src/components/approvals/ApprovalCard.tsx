import { useState } from 'react';
import type { ApprovalRequest } from '../../lib/types';
import { approveRequest, rejectRequest } from '../../api/approvals';
import { useApprovalStore } from '../../stores/approvalStore';
import { AgentAvatar } from '../shared/AgentAvatar';

interface Props {
  approval: ApprovalRequest;
}

export function ApprovalCard({ approval }: Props) {
  const resolveApproval = useApprovalStore((s) => s.resolveApproval);
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);

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
          <h3 className="font-semibold">{approval.title}</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{approval.description}</p>

          {Object.keys(approval.context).length > 0 && (
            <details className="mt-2">
              <summary className="text-xs text-gray-500 cursor-pointer">View context</summary>
              <pre className="mt-1 text-xs bg-white dark:bg-gray-900 rounded p-2 overflow-x-auto">
                {JSON.stringify(approval.context, null, 2)}
              </pre>
            </details>
          )}

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
