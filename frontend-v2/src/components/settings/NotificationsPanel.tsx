import { Loader2 } from 'lucide-react';
import type { NotificationSettings } from '@/lib/types';

interface NotificationsPanelProps {
  settings: NotificationSettings;
  onSave: (updates: Partial<NotificationSettings>) => void;
  isSaving: boolean;
}

interface ToggleProps {
  id: string;
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

function Toggle({ id, label, description, checked, onChange }: ToggleProps) {
  return (
    <div className="flex items-center justify-between py-3">
      <div>
        <label htmlFor={id} className="text-sm font-medium text-foreground cursor-pointer">{label}</label>
        <p className="text-xs text-muted">{description}</p>
      </div>
      <button
        id={id}
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative w-10 h-6 rounded-full transition-colors ${checked ? 'bg-primary' : 'bg-border'}`}
      >
        <span
          className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform ${checked ? 'translate-x-4' : ''}`}
        />
      </button>
    </div>
  );
}

export function NotificationsPanel({ settings, onSave, isSaving }: NotificationsPanelProps) {
  function update(key: keyof NotificationSettings, value: boolean) {
    onSave({ [key]: value });
  }

  return (
    <div role="tabpanel" id="panel-notifications" className="space-y-6">
      <div>
        <h3 className="text-sm font-medium text-foreground mb-1">General</h3>
        <div className="divide-y divide-border">
          <Toggle id="sound" label="Sound" description="Play sounds for notifications" checked={settings.sound_enabled} onChange={(v) => update('sound_enabled', v)} />
          <Toggle id="push" label="Browser Push" description="Show browser push notifications" checked={settings.browser_push_enabled} onChange={(v) => update('browser_push_enabled', v)} />
        </div>
      </div>

      <div>
        <h3 className="text-sm font-medium text-foreground mb-1">Events</h3>
        <div className="divide-y divide-border">
          <Toggle id="approval" label="Approval Requests" description="When an agent needs approval" checked={settings.notify_on_approval} onChange={(v) => update('notify_on_approval', v)} />
          <Toggle id="sprint-complete" label="Sprint Complete" description="When a sprint finishes" checked={settings.notify_on_sprint_complete} onChange={(v) => update('notify_on_sprint_complete', v)} />
          <Toggle id="error" label="Errors" description="When a sprint or task fails" checked={settings.notify_on_error} onChange={(v) => update('notify_on_error', v)} />
          <Toggle id="budget" label="Budget Warnings" description="When approaching budget limits" checked={settings.notify_on_budget_warning} onChange={(v) => update('notify_on_budget_warning', v)} />
        </div>
      </div>

      {isSaving && (
        <div className="flex items-center gap-2 text-xs text-muted">
          <Loader2 size={12} className="animate-spin" />
          Saving...
        </div>
      )}
    </div>
  );
}
