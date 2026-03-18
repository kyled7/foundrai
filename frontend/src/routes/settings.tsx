import { useState, useEffect, useCallback } from 'react';
import { useSearch, useNavigate } from '@tanstack/react-router';
import { useUI } from '@/stores/ui';
import { useSettings, useUpdateSettings, useApiKeys, useAddApiKey, useRemoveApiKey, useTestApiKey } from '@/hooks/use-settings';
import { SettingsTabs, type SettingsTab } from '@/components/settings/SettingsTabs';
import { GeneralSettingsPanel } from '@/components/settings/GeneralSettingsPanel';
import { ApiKeysPanel } from '@/components/settings/ApiKeysPanel';
import { NotificationsPanel } from '@/components/settings/NotificationsPanel';
import { AppearancePanel } from '@/components/settings/AppearancePanel';
import type { GlobalSettings, NotificationSettings } from '@/lib/types';

const DEFAULT_SETTINGS: GlobalSettings = {
  default_model: 'claude-sonnet-4-20250514',
  default_autonomy: 'medium',
  budget_per_sprint_usd: null,
  budget_monthly_usd: null,
  notifications: {
    sound_enabled: true,
    browser_push_enabled: false,
    notify_on_approval: true,
    notify_on_sprint_complete: true,
    notify_on_error: true,
    notify_on_budget_warning: true,
  },
  theme: 'dark',
};

export function SettingsPage() {
  const navigate = useNavigate();
  const search = useSearch({ strict: false }) as Record<string, string>;
  const activeTab = (search.tab as SettingsTab) || 'general';
  const { theme, setTheme, setBreadcrumbs } = useUI();

  const { data: settings } = useSettings();
  const { data: keys } = useApiKeys();
  const updateSettings = useUpdateSettings();
  const addApiKey = useAddApiKey();
  const removeApiKey = useRemoveApiKey();
  const testApiKey = useTestApiKey();

  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [removingProvider, setRemovingProvider] = useState<string | null>(null);

  useEffect(() => {
    setBreadcrumbs([{ label: 'Dashboard', href: '/' }, { label: 'Settings' }]);
  }, [setBreadcrumbs]);

  const handleTabChange = useCallback((tab: SettingsTab) => {
    navigate({ to: '/settings', search: { tab } });
  }, [navigate]);

  function handleSaveGeneral(updates: Partial<GlobalSettings>) {
    updateSettings.mutate(updates);
  }

  function handleSaveNotifications(updates: Partial<NotificationSettings>) {
    updateSettings.mutate({ notifications: { ...(settings?.notifications ?? DEFAULT_SETTINGS.notifications), ...updates } });
  }

  function handleTestKey(provider: string) {
    setTestingProvider(provider);
    testApiKey.mutate(provider, { onSettled: () => setTestingProvider(null) });
  }

  function handleRemoveKey(provider: string) {
    setRemovingProvider(provider);
    removeApiKey.mutate(provider, { onSettled: () => setRemovingProvider(null) });
  }

  const s = settings ?? DEFAULT_SETTINGS;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-foreground mb-6" tabIndex={-1}>Settings</h1>

      <SettingsTabs activeTab={activeTab} onTabChange={handleTabChange} />

      <div className="mt-6">
        {activeTab === 'general' && (
          <GeneralSettingsPanel settings={s} onSave={handleSaveGeneral} isSaving={updateSettings.isPending} />
        )}
        {activeTab === 'api-keys' && (
          <ApiKeysPanel
            keys={keys ?? []}
            onAdd={(provider, key) => addApiKey.mutate({ provider, key })}
            onRemove={handleRemoveKey}
            onTest={handleTestKey}
            isAdding={addApiKey.isPending}
            testingProvider={testingProvider}
            removingProvider={removingProvider}
          />
        )}
        {activeTab === 'notifications' && (
          <NotificationsPanel settings={s.notifications} onSave={handleSaveNotifications} isSaving={updateSettings.isPending} />
        )}
        {activeTab === 'appearance' && (
          <AppearancePanel theme={theme} onThemeChange={setTheme} />
        )}
      </div>
    </div>
  );
}
