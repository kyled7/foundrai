/**
 * Browser notification utility for FoundrAI
 * Handles browser notification API for approval alerts and system events
 */

export type NotificationPermission = 'default' | 'granted' | 'denied';

/**
 * Check if browser notifications are supported
 */
export function isNotificationSupported(): boolean {
  return 'Notification' in window;
}

/**
 * Get current notification permission status
 */
export function getNotificationPermission(): NotificationPermission {
  if (!isNotificationSupported()) {
    return 'denied';
  }
  return Notification.permission as NotificationPermission;
}

/**
 * Request notification permission from the user
 * Returns the granted permission status
 */
export async function requestNotificationPermission(): Promise<NotificationPermission> {
  if (!isNotificationSupported()) {
    throw new Error('Browser notifications are not supported');
  }

  if (Notification.permission === 'granted') {
    return 'granted';
  }

  if (Notification.permission === 'denied') {
    return 'denied';
  }

  try {
    const permission = await Notification.requestPermission();
    return permission as NotificationPermission;
  } catch (err) {
    console.error('Failed to request notification permission:', err);
    return 'denied';
  }
}

export interface ShowNotificationOptions {
  title: string;
  body: string;
  icon?: string;
  badge?: string;
  tag?: string;
  requireInteraction?: boolean;
  silent?: boolean;
  onClick?: () => void;
  onClose?: () => void;
  onError?: (error: Error) => void;
}

/**
 * Show a browser notification
 * Automatically requests permission if not already granted
 */
export async function showNotification(options: ShowNotificationOptions): Promise<Notification | null> {
  if (!isNotificationSupported()) {
    console.warn('Browser notifications are not supported');
    return null;
  }

  // Request permission if needed
  const permission = await requestNotificationPermission();
  if (permission !== 'granted') {
    console.warn('Notification permission not granted');
    return null;
  }

  try {
    const notification = new Notification(options.title, {
      body: options.body,
      icon: options.icon || '/favicon.ico',
      badge: options.badge,
      tag: options.tag,
      requireInteraction: options.requireInteraction || false,
      silent: options.silent || false,
    });

    // Attach event handlers
    if (options.onClick) {
      notification.onclick = () => {
        options.onClick?.();
        notification.close();
      };
    }

    if (options.onClose) {
      notification.onclose = () => options.onClose?.();
    }

    if (options.onError) {
      notification.onerror = (event) => {
        const error = new Error('Notification error');
        options.onError?.(error);
      };
    }

    return notification;
  } catch (err) {
    const error = err instanceof Error ? err : new Error('Failed to show notification');
    console.error('Failed to show notification:', error);
    options.onError?.(error);
    return null;
  }
}

/**
 * Show an approval request notification
 * Specialized notification for approval requests with consistent formatting
 */
export async function showApprovalNotification(
  agentName: string,
  actionType: string,
  title: string,
  onClick?: () => void
): Promise<Notification | null> {
  return showNotification({
    title: `Approval Required: ${agentName}`,
    body: `${actionType}: ${title}`,
    icon: '/favicon.ico',
    tag: 'approval-request',
    requireInteraction: true,
    silent: false,
    onClick,
  });
}

/**
 * Show a sprint completion notification
 */
export async function showSprintCompleteNotification(
  sprintNumber: number,
  goal: string,
  onClick?: () => void
): Promise<Notification | null> {
  return showNotification({
    title: `Sprint ${sprintNumber} Completed`,
    body: goal,
    icon: '/favicon.ico',
    tag: 'sprint-complete',
    requireInteraction: false,
    silent: false,
    onClick,
  });
}

/**
 * Show an error notification
 */
export async function showErrorNotification(
  title: string,
  message: string,
  onClick?: () => void
): Promise<Notification | null> {
  return showNotification({
    title: `Error: ${title}`,
    body: message,
    icon: '/favicon.ico',
    tag: 'error',
    requireInteraction: false,
    silent: false,
    onClick,
  });
}

/**
 * Show a budget warning notification
 */
export async function showBudgetWarningNotification(
  percentageUsed: number,
  onClick?: () => void
): Promise<Notification | null> {
  return showNotification({
    title: 'Budget Warning',
    body: `Sprint has used ${percentageUsed}% of allocated budget`,
    icon: '/favicon.ico',
    tag: 'budget-warning',
    requireInteraction: false,
    silent: false,
    onClick,
  });
}
