import { useRef } from 'react';
import { X, Rocket } from 'lucide-react';
import { useFocusTrap } from '@/hooks/use-focus-trap';

interface WelcomeModalProps {
  open: boolean;
  onClose: () => void;
  onStartTutorial: () => void;
}

export function WelcomeModal({ open, onClose, onStartTutorial }: WelcomeModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  useFocusTrap(modalRef, open);

  if (!open) return null;

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Escape') onClose();
  }

  function handleStartTutorial() {
    onStartTutorial();
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        ref={modalRef}
        role="dialog"
        aria-label="Welcome to FoundrAI"
        aria-modal="true"
        className="bg-card border border-border rounded-lg p-6 w-full max-w-lg mx-4 shadow-xl"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-foreground">Welcome to FoundrAI</h3>
          <button onClick={onClose} aria-label="Close" className="p-1 text-muted hover:text-foreground">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-4">
          <div className="flex flex-col items-center justify-center py-4 text-center">
            <div className="text-4xl mb-4">
              <Rocket className="text-primary" size={48} />
            </div>
            <h4 className="text-xl font-semibold text-foreground mb-2">Your AI-Powered Founding Team</h4>
            <p className="text-muted text-sm max-w-md">
              FoundrAI orchestrates autonomous AI agents working together as an Agile startup team.
              Define your goal, and watch specialized agents (PM, Architect, Developer, QA, Designer, DevOps)
              collaborate to bring it to life.
            </p>
          </div>

          <div className="bg-background border border-border rounded-md p-4 space-y-2">
            <h5 className="text-sm font-semibold text-foreground">What you'll learn:</h5>
            <ul className="text-sm text-muted space-y-1">
              <li>• Setting up your first AI agent team</li>
              <li>• Creating and managing sprints</li>
              <li>• Monitoring agent activity in real-time</li>
              <li>• Configuring API keys and preferences</li>
            </ul>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-muted hover:text-foreground border border-border rounded-md hover:bg-border/50"
            >
              Skip for now
            </button>
            <button
              type="button"
              onClick={handleStartTutorial}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90"
            >
              <Rocket size={14} />
              Start Tutorial
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
