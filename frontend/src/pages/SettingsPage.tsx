import { useEffect, useState } from 'react';
import { listKeys, setKey, deleteKey, validateKeys } from '../api/settings';
import type { KeyStatus, ValidateResponse } from '../api/settings';

const PROVIDER_LABELS: Record<string, string> = {
  anthropic: 'Anthropic (Claude)',
  openai: 'OpenAI',
  google: 'Google (Gemini)',
};

export function SettingsPage() {
  const [keys, setKeys] = useState<KeyStatus[]>([]);
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [validation, setValidation] = useState<Record<string, ValidateResponse>>({});
  const [saving, setSaving] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);

  const loadKeys = () => {
    listKeys()
      .then((data) => setKeys(data.keys))
      .catch(() => {});
  };

  useEffect(() => {
    loadKeys();
  }, []);

  const handleSave = async (provider: string) => {
    const value = inputs[provider];
    if (!value?.trim()) return;
    setSaving(provider);
    try {
      await setKey(provider, value.trim());
      setInputs((prev) => ({ ...prev, [provider]: '' }));
      loadKeys();
    } catch {
      // Error handling could be improved with toast
    } finally {
      setSaving(null);
    }
  };

  const handleDelete = async (provider: string) => {
    try {
      await deleteKey(provider);
      loadKeys();
      setValidation((prev) => {
        const next = { ...prev };
        delete next[provider];
        return next;
      });
    } catch {
      // Error handling could be improved with toast
    }
  };

  const handleValidate = async () => {
    setTesting(true);
    try {
      const results = await validateKeys();
      const map: Record<string, ValidateResponse> = {};
      for (const r of results) {
        map[r.provider] = r;
      }
      setValidation(map);
    } catch {
      // Error handling could be improved with toast
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">API Keys</h2>
          <button
            onClick={handleValidate}
            disabled={testing}
            className="px-3 py-1.5 text-sm rounded bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            {testing ? 'Testing...' : 'Test All Keys'}
          </button>
        </div>
        <p className="text-sm text-gray-500 mb-6">
          Configure API keys for LLM providers. Keys are stored locally and never sent to FoundrAI servers.
        </p>

        <div className="space-y-6">
          {keys.map((k) => (
            <div key={k.provider} className="border-b border-gray-100 dark:border-gray-800 pb-4 last:border-0">
              <div className="flex items-center justify-between mb-2">
                <label className="font-medium text-sm">
                  {PROVIDER_LABELS[k.provider] ?? k.provider}
                </label>
                <div className="flex items-center gap-2">
                  {k.configured && (
                    <span className="text-xs px-2 py-0.5 rounded bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                      Configured
                    </span>
                  )}
                  {validation[k.provider] && (
                    <span
                      className={`text-xs px-2 py-0.5 rounded ${
                        validation[k.provider].valid
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                          : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                      }`}
                    >
                      {validation[k.provider].valid ? 'Valid' : 'Invalid'}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                <input
                  type="password"
                  placeholder={k.configured ? '••••••••••••••••' : `Enter ${k.env_var}`}
                  value={inputs[k.provider] ?? ''}
                  onChange={(e) =>
                    setInputs((prev) => ({ ...prev, [k.provider]: e.target.value }))
                  }
                  className="flex-1 px-3 py-1.5 text-sm rounded border border-gray-300 dark:border-gray-700 bg-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={() => handleSave(k.provider)}
                  disabled={saving === k.provider || !inputs[k.provider]?.trim()}
                  className="px-3 py-1.5 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving === k.provider ? 'Saving...' : 'Save'}
                </button>
                {k.configured && (
                  <button
                    onClick={() => handleDelete(k.provider)}
                    className="px-3 py-1.5 text-sm rounded bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/50"
                  >
                    Remove
                  </button>
                )}
              </div>
              {validation[k.provider]?.error && !validation[k.provider]?.valid && (
                <p className="text-xs text-red-500 mt-1">{validation[k.provider].error}</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
