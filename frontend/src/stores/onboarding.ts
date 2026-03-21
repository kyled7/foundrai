import { create } from 'zustand';

export type OnboardingStep =
  | 'welcome'
  | 'create-project'
  | 'configure-team'
  | 'start-sprint'
  | 'view-results'
  | 'complete';

interface OnboardingState {
  isFirstRun: boolean;
  tutorialActive: boolean;
  currentStep: OnboardingStep;
  completedSteps: Set<OnboardingStep>;
  tooltipsEnabled: boolean;
  dismissedTooltips: Set<string>;

  startTutorial: () => void;
  exitTutorial: () => void;
  setStep: (step: OnboardingStep) => void;
  completeStep: (step: OnboardingStep) => void;
  markFirstRunComplete: () => void;
  dismissTooltip: (tooltipId: string) => void;
  enableTooltips: () => void;
  disableTooltips: () => void;
  resetOnboarding: () => void;
}

const STORAGE_KEY = 'foundrai-onboarding';

interface StoredOnboarding {
  isFirstRun: boolean;
  completedSteps: string[];
  dismissedTooltips: string[];
  tooltipsEnabled: boolean;
}

function loadOnboardingState(): Partial<OnboardingState> {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      return { isFirstRun: true };
    }

    const data: StoredOnboarding = JSON.parse(stored);
    return {
      isFirstRun: data.isFirstRun,
      completedSteps: new Set(data.completedSteps),
      dismissedTooltips: new Set(data.dismissedTooltips),
      tooltipsEnabled: data.tooltipsEnabled,
    };
  } catch {
    return { isFirstRun: true };
  }
}

function saveOnboardingState(state: OnboardingState) {
  try {
    const data: StoredOnboarding = {
      isFirstRun: state.isFirstRun,
      completedSteps: Array.from(state.completedSteps),
      dismissedTooltips: Array.from(state.dismissedTooltips),
      tooltipsEnabled: state.tooltipsEnabled,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {
    // Silently fail if localStorage is unavailable
  }
}

const persistedState = loadOnboardingState();

const initialState = {
  isFirstRun: persistedState.isFirstRun ?? true,
  tutorialActive: false,
  currentStep: 'welcome' as OnboardingStep,
  completedSteps: persistedState.completedSteps ?? new Set<OnboardingStep>(),
  tooltipsEnabled: persistedState.tooltipsEnabled ?? true,
  dismissedTooltips: persistedState.dismissedTooltips ?? new Set<string>(),
};

export const useOnboarding = create<OnboardingState>((set, get) => ({
  ...initialState,

  startTutorial: () => {
    set({
      tutorialActive: true,
      currentStep: 'welcome'
    });
  },

  exitTutorial: () => {
    set({ tutorialActive: false });
    saveOnboardingState(get());
  },

  setStep: (step) => {
    set({ currentStep: step });
  },

  completeStep: (step) => {
    set((state) => {
      const newCompletedSteps = new Set(state.completedSteps);
      newCompletedSteps.add(step);

      // Auto-advance to next step
      const stepOrder: OnboardingStep[] = [
        'welcome',
        'create-project',
        'configure-team',
        'start-sprint',
        'view-results',
        'complete'
      ];

      const currentIndex = stepOrder.indexOf(step);
      const nextStep = stepOrder[currentIndex + 1] || 'complete';

      return {
        completedSteps: newCompletedSteps,
        currentStep: nextStep,
      };
    });
    saveOnboardingState(get());
  },

  markFirstRunComplete: () => {
    set({ isFirstRun: false });
    saveOnboardingState(get());
  },

  dismissTooltip: (tooltipId) => {
    set((state) => {
      const newDismissedTooltips = new Set(state.dismissedTooltips);
      newDismissedTooltips.add(tooltipId);
      return { dismissedTooltips: newDismissedTooltips };
    });
    saveOnboardingState(get());
  },

  enableTooltips: () => {
    set({ tooltipsEnabled: true });
    saveOnboardingState(get());
  },

  disableTooltips: () => {
    set({ tooltipsEnabled: false });
    saveOnboardingState(get());
  },

  resetOnboarding: () => {
    set({
      ...initialState,
      isFirstRun: true,
      completedSteps: new Set(),
      dismissedTooltips: new Set(),
      tutorialActive: false,
    });
    saveOnboardingState(get());
  },
}));
