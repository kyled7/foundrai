import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { X, ChevronLeft, ChevronRight, BookOpen } from 'lucide-react';
import { useOnboarding, type OnboardingStep } from '@/stores/onboarding';
import { cn } from '@/lib/utils';

interface TutorialStepConfig {
  step: OnboardingStep;
  title: string;
  description: string;
  targetSelector: string | null;
  placement: 'top' | 'bottom' | 'left' | 'right';
}

const TUTORIAL_STEPS: TutorialStepConfig[] = [
  {
    step: 'welcome',
    title: 'Welcome to FoundrAI!',
    description:
      'This tutorial will guide you through creating your first AI-powered project. Let\'s get started!',
    targetSelector: null,
    placement: 'bottom',
  },
  {
    step: 'create-project',
    title: 'Create a Project',
    description:
      'Click "New Project" to set up your first AI agent team. You can use our sample goal to see FoundrAI in action.',
    targetSelector: '[data-tutorial="create-project"]',
    placement: 'bottom',
  },
  {
    step: 'configure-team',
    title: 'Configure Your Team',
    description:
      'Choose which AI agents to include in your team. Each agent has a specialized role — PM, Architect, Developer, QA, and more.',
    targetSelector: '[data-tutorial="configure-team"]',
    placement: 'bottom',
  },
  {
    step: 'start-sprint',
    title: 'Start a Sprint',
    description:
      'Once your project is set up, start a sprint. Your AI agents will collaborate to decompose the goal, plan tasks, and execute.',
    targetSelector: '[data-tutorial="start-sprint"]',
    placement: 'bottom',
  },
  {
    step: 'view-results',
    title: 'View Results',
    description:
      'Watch your agents work in real-time on the sprint board. Track progress, view agent communications, and review completed tasks.',
    targetSelector: '[data-tutorial="view-results"]',
    placement: 'top',
  },
];

interface HighlightRect {
  top: number;
  left: number;
  width: number;
  height: number;
}

function getElementRect(selector: string): HighlightRect | null {
  const el = document.querySelector(selector);
  if (!el) return null;
  const rect = el.getBoundingClientRect();
  return {
    top: rect.top - 8,
    left: rect.left - 8,
    width: rect.width + 16,
    height: rect.height + 16,
  };
}

export function TutorialOverlay() {
  const { tutorialActive, currentStep, completeStep, exitTutorial, setStep } =
    useOnboarding();
  const [highlightRect, setHighlightRect] = useState<HighlightRect | null>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const currentStepIndex = useMemo(
    () => TUTORIAL_STEPS.findIndex((s) => s.step === currentStep),
    [currentStep]
  );

  const stepConfig = TUTORIAL_STEPS[currentStepIndex] ?? null;

  // Update highlight position when step changes
  useEffect(() => {
    if (!tutorialActive || !stepConfig) return;

    function updateRect() {
      if (stepConfig.targetSelector) {
        setHighlightRect(getElementRect(stepConfig.targetSelector));
      } else {
        setHighlightRect(null);
      }
    }

    updateRect();
    window.addEventListener('resize', updateRect);
    window.addEventListener('scroll', updateRect, true);

    return () => {
      window.removeEventListener('resize', updateRect);
      window.removeEventListener('scroll', updateRect, true);
    };
  }, [tutorialActive, stepConfig]);

  const handleNext = useCallback(() => {
    if (!stepConfig) return;
    completeStep(stepConfig.step);
    if (currentStepIndex >= TUTORIAL_STEPS.length - 1) {
      exitTutorial();
    }
  }, [stepConfig, currentStepIndex, completeStep, exitTutorial]);

  const handlePrevious = useCallback(() => {
    if (currentStepIndex <= 0) return;
    const prevStep = TUTORIAL_STEPS[currentStepIndex - 1];
    setStep(prevStep.step);
  }, [currentStepIndex, setStep]);

  const handleSkip = useCallback(() => {
    exitTutorial();
  }, [exitTutorial]);

  // Escape key to skip
  useEffect(() => {
    if (!tutorialActive) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') exitTutorial();
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [tutorialActive, exitTutorial]);

  if (!tutorialActive || !stepConfig) return null;

  const isFirstStep = currentStepIndex === 0;
  const isLastStep = currentStepIndex === TUTORIAL_STEPS.length - 1;
  const progress = ((currentStepIndex + 1) / TUTORIAL_STEPS.length) * 100;

  // Compute tooltip position
  const tooltipStyle: React.CSSProperties = {};
  if (highlightRect) {
    const padding = 12;
    switch (stepConfig.placement) {
      case 'bottom':
        tooltipStyle.top = highlightRect.top + highlightRect.height + padding;
        tooltipStyle.left = highlightRect.left + highlightRect.width / 2;
        tooltipStyle.transform = 'translateX(-50%)';
        break;
      case 'top':
        tooltipStyle.bottom =
          window.innerHeight - highlightRect.top + padding;
        tooltipStyle.left = highlightRect.left + highlightRect.width / 2;
        tooltipStyle.transform = 'translateX(-50%)';
        break;
      case 'left':
        tooltipStyle.top = highlightRect.top + highlightRect.height / 2;
        tooltipStyle.right =
          window.innerWidth - highlightRect.left + padding;
        tooltipStyle.transform = 'translateY(-50%)';
        break;
      case 'right':
        tooltipStyle.top = highlightRect.top + highlightRect.height / 2;
        tooltipStyle.left = highlightRect.left + highlightRect.width + padding;
        tooltipStyle.transform = 'translateY(-50%)';
        break;
    }
  } else {
    // Center on screen for steps without a target element
    tooltipStyle.top = '50%';
    tooltipStyle.left = '50%';
    tooltipStyle.transform = 'translate(-50%, -50%)';
  }

  return (
    <div className="fixed inset-0 z-[60]" aria-label="Tutorial overlay">
      {/* Semi-transparent backdrop */}
      <div className="absolute inset-0 bg-black/40" onClick={handleSkip} />

      {/* Highlight cutout */}
      {highlightRect && (
        <div
          className="absolute border-2 border-primary rounded-lg bg-transparent z-[61]"
          style={{
            top: highlightRect.top,
            left: highlightRect.left,
            width: highlightRect.width,
            height: highlightRect.height,
            boxShadow: '0 0 0 9999px rgba(0,0,0,0.4)',
          }}
        />
      )}

      {/* Tooltip card */}
      <div
        ref={tooltipRef}
        role="dialog"
        aria-label={stepConfig.title}
        className="absolute z-[62] bg-card border border-border rounded-lg shadow-xl w-80 p-4"
        style={tooltipStyle}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <BookOpen size={16} className="text-primary" />
            <span className="text-xs font-medium text-muted">
              Step {currentStepIndex + 1} of {TUTORIAL_STEPS.length}
            </span>
          </div>
          <button
            onClick={handleSkip}
            aria-label="Skip tutorial"
            className="p-1 text-muted hover:text-foreground"
          >
            <X size={14} />
          </button>
        </div>

        {/* Content */}
        <h4 className="text-sm font-semibold text-foreground mb-1">
          {stepConfig.title}
        </h4>
        <p className="text-xs text-muted mb-4">{stepConfig.description}</p>

        {/* Progress bar */}
        <div className="w-full h-1 bg-border rounded-full mb-3">
          <div
            className="h-1 bg-primary rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between">
          <button
            onClick={handleSkip}
            className="text-xs text-muted hover:text-foreground"
          >
            Skip tutorial
          </button>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrevious}
              disabled={isFirstStep}
              className={cn(
                'flex items-center gap-1 px-2 py-1 text-xs rounded border border-border',
                isFirstStep
                  ? 'text-muted/50 cursor-not-allowed'
                  : 'text-foreground hover:bg-border/50'
              )}
            >
              <ChevronLeft size={12} />
              Back
            </button>
            <button
              onClick={handleNext}
              className="flex items-center gap-1 px-3 py-1 text-xs font-medium rounded bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {isLastStep ? 'Finish' : 'Next'}
              {!isLastStep && <ChevronRight size={12} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
