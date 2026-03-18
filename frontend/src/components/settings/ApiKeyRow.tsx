import { Loader2, CheckCircle, XCircle, CircleDashed, Trash2, FlaskConical } from 'lucide-react';
import type { ApiKeyInfo } from '@/lib/types';

interface ApiKeyRowProps {
  keyInfo: ApiKeyInfo;
  onTest: (provider: string) => void;
  onRemove: (provider: string) => void;
  isTesting: boolean;
  isRemoving: boolean;
}

function ValidationIcon({ status }: { status: boolean | null }) {
  if (status === true) return <CheckCircle size={16} className="text-success" />;
  if (status === false) return <XCircle size={16} className="text-destructive" />;
  return <CircleDashed size={16} className="text-muted" />;
}

function validationLabel(status: boolean | null): string {
  if (status === true) return 'Valid';
  if (status === false) return 'Invalid';
  return 'Untested';
}

export function ApiKeyRow({ keyInfo, onTest, onRemove, isTesting, isRemoving }: ApiKeyRowProps) {
  return (
    <div className="flex items-center justify-between gap-4 px-4 py-3 bg-background border border-border rounded-md">
      <div className="flex items-center gap-4 min-w-0">
        <span className="text-sm font-medium text-foreground capitalize w-24 shrink-0">
          {keyInfo.provider}
        </span>
        <code className="text-xs text-muted font-mono truncate">{keyInfo.masked_key}</code>
        <div className="flex items-center gap-1.5 shrink-0">
          <ValidationIcon status={keyInfo.is_valid} />
          <span className="text-xs text-muted">{validationLabel(keyInfo.is_valid)}</span>
        </div>
      </div>

      <div className="flex items-center gap-1 shrink-0">
        <button
          onClick={() => onTest(keyInfo.provider)}
          disabled={isTesting}
          aria-label={`Test ${keyInfo.provider} API key`}
          className="p-2 text-muted hover:text-foreground rounded-md hover:bg-border/50 disabled:opacity-50"
        >
          {isTesting ? <Loader2 size={14} className="animate-spin" /> : <FlaskConical size={14} />}
        </button>
        <button
          onClick={() => onRemove(keyInfo.provider)}
          disabled={isRemoving}
          aria-label={`Remove ${keyInfo.provider} API key`}
          className="p-2 text-muted hover:text-destructive rounded-md hover:bg-border/50 disabled:opacity-50"
        >
          {isRemoving ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
        </button>
      </div>
    </div>
  );
}
