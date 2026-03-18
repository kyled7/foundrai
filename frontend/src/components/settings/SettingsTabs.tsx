import { cn } from '@/lib/utils';
import { Settings, Key, Bell, Palette } from 'lucide-react';

export type SettingsTab = 'general' | 'api-keys' | 'notifications' | 'appearance';

interface SettingsTabsProps {
  activeTab: SettingsTab;
  onTabChange: (tab: SettingsTab) => void;
}

const tabs: { id: SettingsTab; label: string; icon: typeof Settings }[] = [
  { id: 'general', label: 'General', icon: Settings },
  { id: 'api-keys', label: 'API Keys', icon: Key },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'appearance', label: 'Appearance', icon: Palette },
];

export function SettingsTabs({ activeTab, onTabChange }: SettingsTabsProps) {
  function handleKeyDown(e: React.KeyboardEvent) {
    const currentIndex = tabs.findIndex((t) => t.id === activeTab);
    if (e.key === 'ArrowRight') {
      e.preventDefault();
      const next = tabs[(currentIndex + 1) % tabs.length];
      onTabChange(next.id);
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      const prev = tabs[(currentIndex - 1 + tabs.length) % tabs.length];
      onTabChange(prev.id);
    }
  }

  return (
    <div
      role="tablist"
      aria-label="Settings sections"
      className="flex gap-1 border-b border-border overflow-x-auto"
      onKeyDown={handleKeyDown}
    >
      {tabs.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          role="tab"
          aria-selected={activeTab === id}
          aria-controls={`panel-${id}`}
          tabIndex={activeTab === id ? 0 : -1}
          onClick={() => onTabChange(id)}
          className={cn(
            'flex items-center gap-2 px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors border-b-2 -mb-px',
            activeTab === id
              ? 'border-primary text-primary'
              : 'border-transparent text-muted hover:text-foreground hover:border-border'
          )}
        >
          <Icon size={16} />
          {label}
        </button>
      ))}
    </div>
  );
}
