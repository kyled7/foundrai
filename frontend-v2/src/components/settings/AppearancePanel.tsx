import { Monitor, Moon, Sun } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Theme } from '@/stores/ui';

interface AppearancePanelProps {
  theme: Theme;
  onThemeChange: (theme: Theme) => void;
}

const themes: { value: Theme; label: string; icon: typeof Moon; description: string }[] = [
  { value: 'dark', label: 'Dark', icon: Moon, description: 'Dark background with light text' },
  { value: 'light', label: 'Light', icon: Sun, description: 'Light background with dark text' },
  { value: 'system', label: 'System', icon: Monitor, description: 'Follow your OS preference' },
];

export function AppearancePanel({ theme, onThemeChange }: AppearancePanelProps) {
  return (
    <div role="tabpanel" id="panel-appearance" className="space-y-4">
      <div>
        <h3 className="text-sm font-medium text-foreground">Theme</h3>
        <p className="text-xs text-muted mt-1">Choose how FoundrAI looks to you</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-lg">
        {themes.map(({ value, label, icon: Icon, description }) => (
          <button
            key={value}
            onClick={() => onThemeChange(value)}
            className={cn(
              'flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-colors',
              theme === value
                ? 'border-primary bg-primary/10'
                : 'border-border hover:border-muted bg-background'
            )}
          >
            <Icon size={24} className={theme === value ? 'text-primary' : 'text-muted'} />
            <span className="text-sm font-medium text-foreground">{label}</span>
            <span className="text-xs text-muted text-center">{description}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
