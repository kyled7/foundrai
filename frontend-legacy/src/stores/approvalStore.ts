import { create } from 'zustand';
import type { ApprovalRequest, ApprovalStatus } from '../types';

interface ApprovalStore {
  approvals: ApprovalRequest[];
  pendingCount: number;

  setApprovals: (approvals: ApprovalRequest[]) => void;
  addApproval: (approval: ApprovalRequest) => void;
  resolveApproval: (approvalId: string, status: ApprovalStatus) => void;
}

export const useApprovalStore = create<ApprovalStore>((set) => ({
  approvals: [],
  pendingCount: 0,

  setApprovals: (approvals) =>
    set({
      approvals,
      pendingCount: approvals.filter((a) => a.status === 'pending').length,
    }),

  addApproval: (approval) =>
    set((state) => ({
      approvals: [approval, ...state.approvals],
      pendingCount: state.pendingCount + 1,
    })),

  resolveApproval: (approvalId, status) =>
    set((state) => ({
      approvals: state.approvals.map((a) =>
        a.approval_id === approvalId ? { ...a, status } : a
      ),
      pendingCount: Math.max(0, state.pendingCount - 1),
    })),
}));
