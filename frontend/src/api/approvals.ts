import { api } from './client';
import type { ApprovalRequest } from '../types';

interface ApprovalListResponse {
  approvals: ApprovalRequest[];
  pending_count: number;
  total: number;
}

export async function listApprovals(sprintId: string): Promise<ApprovalListResponse> {
  return api.get(`/sprints/${sprintId}/approvals`);
}

export async function getApproval(approvalId: string): Promise<ApprovalRequest> {
  return api.get(`/approvals/${approvalId}`);
}

export async function approveRequest(approvalId: string, comment = ''): Promise<void> {
  await api.post(`/approvals/${approvalId}/approve`, { comment });
}

export async function rejectRequest(approvalId: string, comment = ''): Promise<void> {
  await api.post(`/approvals/${approvalId}/reject`, { comment });
}
