import { Check, Circle } from 'lucide-react';
import { useOnboarding, type OnboardingStep } from '@/stores/onboarding';
import { cn } from '@/lib/utils';

interface StepInfo {
  step: OnboardingStep;
  label: string;
}

const ONBOARDING_STEPS: StepInfo[] = [
  { step: 'welcome', label: 'Welcome' },
  { step: 'create-project', label: 'Create Project' },
  { step: 'configure-team', label: 'Configure Team' },
  { step: 'start-sprint', label: 'Start Sprint' },
  { step: 'view-results', label: 'View Results' },
];

export function ProgressIndicator() {
  const { completedSteps, currentStep, tutorialActive } = useOnboarding();

  const completedCount = ONBOARDING_STEPS.filter((s) =>
    completedSteps.has(s.step)
  ).length;
  const progress = Math.round((completedCount / ONBOARDING_STEPS.length) * 100);

  if (!tutorialActive && completedCount === 0) return null;
  if (completedSteps.has('complete')) return null;

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-foreground">
          Getting Started
        </h3>
        <span className="text-xs text-muted">{progress}% complete</span>
      </div>

      {/* Progress bar */}
      <div className="w-full h-1.5 bg-border rounded-full mb-4">
        <div
          className="h-1.5 bg-primary rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Steps checklist */}
      <ul className="space-y-2">
        {ONBOARDING_STEPS.map(({ step, label }) => {
          const isCompleted = completedSteps.has(step);
          const isCurrent = currentStep === step && tutorialActive;

          return (
            <li key={step} className="flex items-center gap-2">
              {isCompleted ? (
                <div className="w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                  <Check size={12} className="text-primary-foreground" />
                </div>
              ) : (
                <div
                  className={cn(
                    'w-5 h-5 rounded-full border-2 flex items-center justify-center',
                    isCurrent
                      ? 'border-primary'
                      : 'border-border'
                  )}
                >
                  {isCurrent && (
                    <Circle size={8} className="text-primary fill-primary" />
                  )}
                </div>
              )}
              <span
                className={cn(
                  'text-xs',
                  isCompleted
                    ? 'text-foreground'
                    : isCurrent
                      ? 'text-foreground font-medium'
                      : 'text-muted'
                )}
              >
                {label}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
