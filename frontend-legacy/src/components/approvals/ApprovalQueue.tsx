import { useApprovalStore } from '../../stores/approvalStore';
import { ApprovalCard } from './ApprovalCard';

export function ApprovalQueue() {
  const approvals = useApprovalStore((s) => s.approvals);
  const pending = approvals.filter((a) => a.status === 'pending');

  if (pending.length === 0) {
    return (
      <div className="p-4 text-center text-gray-400">
        No pending approvals
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {pending.map((a) => (
        <ApprovalCard key={a.approval_id} approval={a} />
      ))}
    </div>
  );
}
