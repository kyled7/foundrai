import { useState } from 'react';
import { Send } from 'lucide-react';

interface SprintChatProps {
  onSend: (message: string, targetAgent?: string) => void;
  agents?: string[];
  disabled?: boolean;
}

export function SprintChat({ onSend, agents = [], disabled }: SprintChatProps) {
  const [message, setMessage] = useState('');
  const [target, setTarget] = useState<string>('all');

  const handleSend = () => {
    if (!message.trim() || disabled) return;
    onSend(message.trim(), target === 'all' ? undefined : target);
    setMessage('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-border px-4 py-3 flex items-center gap-2">
      {agents.length > 0 && (
        <select
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          className="bg-background border border-border rounded-md px-2 py-1.5 text-xs text-muted shrink-0"
        >
          <option value="all">All</option>
          {agents.map(a => (
            <option key={a} value={a}>{a.replace('_', ' ')}</option>
          ))}
        </select>
      )}
      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Send instruction to team..."
        disabled={disabled}
        className="flex-1 bg-background border border-border rounded-md px-3 py-1.5 text-sm text-foreground placeholder:text-muted disabled:opacity-50"
      />
      <button
        onClick={handleSend}
        disabled={!message.trim() || disabled}
        className="p-2 bg-primary text-primary-foreground rounded-md hover:opacity-90 disabled:opacity-50"
      >
        <Send size={14} />
      </button>
    </div>
  );
}
