import { create } from 'zustand';
import type { ApprovalRequest, ApprovalStatus } from '../lib/types';
import { showApprovalNotification } from '../utils/notifications';
import { playNotificationSound } from '../utils/sound';
import { api } from '../lib/api';

interface ApprovalStore {
  approvals: ApprovalRequest[];
  pendingCount: number;

  setApprovals: (approvals: ApprovalRequest[]) => void;
  addApproval: (approval: ApprovalRequest) => void;
  resolveApproval: (approvalId: string, status: ApprovalStatus) => void;
}

/**
 * Trigger notification for a new approval request
 * Checks user settings before showing notification or playing sound
 */
async function triggerApprovalNotification(approval: ApprovalRequest): Promise<void> {
  try {
    // Fetch current settings to check notification preferences
    const settings = await api.settings.get();

    // Only proceed if user has approval notifications enabled
    if (!settings.notifications.notify_on_approval) {
      return;
    }

    // Show browser notification if enabled
    if (settings.notifications.browser_push_enabled) {
      await showApprovalNotification(
        approval.agent_id,
        approval.action_type,
        approval.title
      );
    }

    // Play sound if enabled
    if (settings.notifications.sound_enabled) {
      await playNotificationSound();
    }
  } catch (err) {
    // Silently fail - notifications are non-critical
    // User will still see the approval in the UI
    console.error('Failed to trigger approval notification:', err);
  }
}

export const useApprovalStore = create<ApprovalStore>((set) => ({
  approvals: [],
  pendingCount: 0,

  setApprovals: (approvals) =>
    set({
      approvals,
      pendingCount: approvals.filter((a) => a.status === 'pending').length,
    }),

  addApproval: (approval) => {
    set((state) => ({
      approvals: [approval, ...state.approvals],
      pendingCount: state.pendingCount + 1,
    }));

    // Trigger notification asynchronously (non-blocking)
    triggerApprovalNotification(approval);
  },

  resolveApproval: (approvalId, status) =>
    set((state) => ({
      approvals: state.approvals.map((a) =>
        a.approval_id === approvalId ? { ...a, status } : a
      ),
      pendingCount: Math.max(0, state.pendingCount - 1),
    })),
}));
