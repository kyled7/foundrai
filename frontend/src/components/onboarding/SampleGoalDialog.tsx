import { useRef } from 'react';
import { Rocket, PenLine, X } from 'lucide-react';
import { useFocusTrap } from '@/hooks/use-focus-trap';
import { SAMPLE_WIZARD_STEP1 } from '@/lib/sample-goals';
import type { WizardStep1Data } from '@/lib/schemas';

interface SampleGoalDialogProps {
  open: boolean;
  onClose: () => void;
  onUseSampleGoal: (data: WizardStep1Data) => void;
  onCreateCustom: () => void;
}

export function SampleGoalDialog({ open, onClose, onUseSampleGoal, onCreateCustom }: SampleGoalDialogProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  useFocusTrap(modalRef, open);

  if (!open) return null;

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Escape') onClose();
  }

  function handleUseSample() {
    onUseSampleGoal(SAMPLE_WIZARD_STEP1);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        ref={modalRef}
        role="dialog"
        aria-label="Choose a starting point"
        aria-modal="true"
        className="bg-card border border-border rounded-lg p-6 w-full max-w-lg mx-4 shadow-xl"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-foreground">How would you like to start?</h3>
          <button onClick={onClose} aria-label="Close" className="p-1 text-muted hover:text-foreground">
            <X size={18} />
          </button>
        </div>

        <p className="text-sm text-muted mb-6">
          Choose a sample project to see FoundrAI in action, or start from scratch with your own idea.
        </p>

        <div className="space-y-3">
          <button
            onClick={handleUseSample}
            className="w-full flex items-start gap-4 p-4 border-2 border-primary/50 bg-primary/5 rounded-lg text-left hover:bg-primary/10 hover:border-primary transition-colors"
          >
            <div className="mt-0.5 p-2 bg-primary/10 rounded-md">
              <Rocket size={20} className="text-primary" />
            </div>
            <div>
              <div className="font-medium text-foreground">Try the sample project</div>
              <div className="text-sm text-muted mt-1">
                Build a &ldquo;Hello World API&rdquo; &mdash; see how AI agents collaborate to plan, code, test, and document a project.
              </div>
              <div className="text-xs text-primary mt-2 font-medium">Recommended for first-time users</div>
            </div>
          </button>

          <button
            onClick={onCreateCustom}
            className="w-full flex items-start gap-4 p-4 border border-border rounded-lg text-left hover:bg-border/30 transition-colors"
          >
            <div className="mt-0.5 p-2 bg-border/50 rounded-md">
              <PenLine size={20} className="text-muted" />
            </div>
            <div>
              <div className="font-medium text-foreground">Start from scratch</div>
              <div className="text-sm text-muted mt-1">
                Define your own project goal and configure the team to match your needs.
              </div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
