import { useState } from 'react';
import { Plus } from 'lucide-react';
import type { ApiKeyInfo } from '@/lib/types';
import { ApiKeyRow } from './ApiKeyRow';
import { AddApiKeyModal } from './AddApiKeyModal';

interface ApiKeysPanelProps {
  keys: ApiKeyInfo[];
  onAdd: (provider: string, key: string) => void;
  onRemove: (provider: string) => void;
  onTest: (provider: string) => void;
  isAdding: boolean;
  testingProvider: string | null;
  removingProvider: string | null;
}

export function ApiKeysPanel({
  keys, onAdd, onRemove, onTest, isAdding, testingProvider, removingProvider,
}: ApiKeysPanelProps) {
  const [modalOpen, setModalOpen] = useState(false);

  function handleAdd(provider: string, key: string) {
    onAdd(provider, key);
    setModalOpen(false);
  }

  return (
    <div role="tabpanel" id="panel-api-keys" className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium text-foreground">API Keys</h3>
          <p className="text-xs text-muted mt-1">Manage API keys for LLM providers</p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="flex items-center gap-1.5 px-3 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90"
        >
          <Plus size={14} />
          Add API Key
        </button>
      </div>

      {keys.length === 0 ? (
        <p className="text-sm text-muted py-8 text-center">No API keys configured</p>
      ) : (
        <div className="space-y-2">
          {keys.map((k) => (
            <ApiKeyRow
              key={k.provider}
              keyInfo={k}
              onTest={onTest}
              onRemove={onRemove}
              isTesting={testingProvider === k.provider}
              isRemoving={removingProvider === k.provider}
            />
          ))}
        </div>
      )}

      <AddApiKeyModal open={modalOpen} onClose={() => setModalOpen(false)} onAdd={handleAdd} isAdding={isAdding} />
    </div>
  );
}
