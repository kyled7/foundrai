import { useState, useRef } from 'react';
import { X, Loader2 } from 'lucide-react';
import { useFocusTrap } from '@/hooks/use-focus-trap';

interface AddApiKeyModalProps {
  open: boolean;
  onClose: () => void;
  onAdd: (provider: string, key: string) => void;
  isAdding: boolean;
}

const providers = [
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'custom', label: 'Custom' },
];

export function AddApiKeyModal({ open, onClose, onAdd, isAdding }: AddApiKeyModalProps) {
  const [provider, setProvider] = useState('anthropic');
  const [key, setKey] = useState('');
  const modalRef = useRef<HTMLDivElement>(null);

  useFocusTrap(modalRef, open);

  if (!open) return null;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!key.trim()) return;
    onAdd(provider, key.trim());
    setKey('');
    setProvider('anthropic');
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Escape') onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        ref={modalRef}
        role="dialog"
        aria-label="Add API key"
        aria-modal="true"
        className="bg-card border border-border rounded-lg p-6 w-full max-w-md mx-4 shadow-xl"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-foreground">Add API Key</h3>
          <button onClick={onClose} aria-label="Close" className="p-1 text-muted hover:text-foreground">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label htmlFor="provider" className="text-sm font-medium text-foreground">Provider</label>
            <select
              id="provider"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {providers.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label htmlFor="api-key" className="text-sm font-medium text-foreground">API Key</label>
            <input
              id="api-key"
              type="password"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder="sk-..."
              autoComplete="off"
              className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-muted hover:text-foreground border border-border rounded-md hover:bg-border/50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!key.trim() || isAdding}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isAdding && <Loader2 size={14} className="animate-spin" />}
              Add Key
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
