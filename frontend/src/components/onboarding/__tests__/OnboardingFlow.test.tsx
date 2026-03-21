import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { useOnboarding } from '@/stores/onboarding';
import { WelcomeModal } from '../WelcomeModal';
import { TutorialOverlay } from '../TutorialOverlay';
import { ProgressIndicator } from '../ProgressIndicator';

// Mock the focus trap hook
vi.mock('../../../hooks/use-focus-trap', () => ({
  useFocusTrap: vi.fn(),
}));

// Mock cn utility
vi.mock('../../../lib/utils', () => ({
  cn: (...args: unknown[]) => args.filter(Boolean).join(' '),
}));

describe('End-to-End Onboarding Flow', () => {
  beforeEach(() => {
    // Reset onboarding store to fresh state
    useOnboarding.setState({
      isFirstRun: true,
      tutorialActive: false,
      currentStep: 'welcome',
      completedSteps: new Set(),
      tooltipsEnabled: true,
      dismissedTooltips: new Set(),
    });
    localStorage.clear();
  });

  describe('1. First-run detection', () => {
    it('should show WelcomeModal when isFirstRun is true', () => {
      const state = useOnboarding.getState();
      expect(state.isFirstRun).toBe(true);

      render(
        <WelcomeModal
          open={true}
          onClose={vi.fn()}
          onStartTutorial={vi.fn()}
        />
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/your ai-powered founding team/i)).toBeInTheDocument();
    });

    it('should not show WelcomeModal after first run is marked complete', () => {
      useOnboarding.getState().markFirstRunComplete();
      const state = useOnboarding.getState();
      expect(state.isFirstRun).toBe(false);
    });
  });

  describe('2. Start Tutorial flow', () => {
    it('should activate tutorial when startTutorial is called', () => {
      useOnboarding.getState().startTutorial();
      const state = useOnboarding.getState();
      expect(state.tutorialActive).toBe(true);
      expect(state.currentStep).toBe('welcome');
    });

    it('should render TutorialOverlay when tutorial is active', () => {
      useOnboarding.getState().startTutorial();

      render(<TutorialOverlay />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Welcome to FoundrAI!')).toBeInTheDocument();
      expect(screen.getByText('Step 1 of 5')).toBeInTheDocument();
    });

    it('should not render TutorialOverlay when tutorial is inactive', () => {
      render(<TutorialOverlay />);
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  describe('3. Tutorial step progression', () => {
    beforeEach(() => {
      useOnboarding.getState().startTutorial();
    });

    it('should advance through steps with Next button', () => {
      const { rerender } = render(<TutorialOverlay />);

      // Step 1: Welcome
      expect(screen.getByText('Welcome to FoundrAI!')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Next'));
      rerender(<TutorialOverlay />);

      // Step 2: Create Project
      expect(screen.getByText('Create a Project')).toBeInTheDocument();
      expect(screen.getByText('Step 2 of 5')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Next'));
      rerender(<TutorialOverlay />);

      // Step 3: Configure Team
      expect(screen.getByText('Configure Your Team')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Next'));
      rerender(<TutorialOverlay />);

      // Step 4: Start Sprint
      expect(screen.getByText('Start a Sprint')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Next'));
      rerender(<TutorialOverlay />);

      // Step 5: View Results (last step shows "Finish")
      expect(screen.getByText('View Results')).toBeInTheDocument();
      expect(screen.getByText('Finish')).toBeInTheDocument();
    });

    it('should complete tutorial on Finish', () => {
      const { rerender } = render(<TutorialOverlay />);

      // Advance through all steps
      for (let i = 0; i < 4; i++) {
        fireEvent.click(screen.getByText('Next'));
        rerender(<TutorialOverlay />);
      }

      // Click Finish
      fireEvent.click(screen.getByText('Finish'));
      const state = useOnboarding.getState();
      expect(state.tutorialActive).toBe(false);
      expect(state.completedSteps.has('view-results')).toBe(true);
    });

    it('should navigate back with Previous button', () => {
      const { rerender } = render(<TutorialOverlay />);

      // Advance to step 2
      fireEvent.click(screen.getByText('Next'));
      rerender(<TutorialOverlay />);
      expect(screen.getByText('Create a Project')).toBeInTheDocument();

      // Go back
      fireEvent.click(screen.getByText('Back'));
      rerender(<TutorialOverlay />);
      expect(screen.getByText('Welcome to FoundrAI!')).toBeInTheDocument();
    });
  });

  describe('4. Tutorial skip functionality', () => {
    it('should skip tutorial via Skip button', () => {
      useOnboarding.getState().startTutorial();

      render(<TutorialOverlay />);

      fireEvent.click(screen.getByText('Skip tutorial'));

      const state = useOnboarding.getState();
      expect(state.tutorialActive).toBe(false);
    });

    it('should skip tutorial via Escape key', () => {
      useOnboarding.getState().startTutorial();

      render(<TutorialOverlay />);

      fireEvent.keyDown(window, { key: 'Escape' });

      const state = useOnboarding.getState();
      expect(state.tutorialActive).toBe(false);
    });
  });

  describe('5. Progress indicator', () => {
    it('should not render when no steps completed and tutorial inactive', () => {
      render(<ProgressIndicator />);
      expect(screen.queryByText('Getting Started')).not.toBeInTheDocument();
    });

    it('should render during active tutorial', () => {
      useOnboarding.getState().startTutorial();

      render(<ProgressIndicator />);

      expect(screen.getByText('Getting Started')).toBeInTheDocument();
      expect(screen.getByText('0% complete')).toBeInTheDocument();
    });

    it('should update progress as steps are completed', () => {
      useOnboarding.getState().startTutorial();
      useOnboarding.getState().completeStep('welcome');

      const { rerender } = render(<ProgressIndicator />);

      expect(screen.getByText('20% complete')).toBeInTheDocument();

      useOnboarding.getState().completeStep('create-project');
      rerender(<ProgressIndicator />);

      expect(screen.getByText('40% complete')).toBeInTheDocument();
    });

    it('should show all 5 step labels', () => {
      useOnboarding.getState().startTutorial();

      render(<ProgressIndicator />);

      expect(screen.getByText('Welcome')).toBeInTheDocument();
      expect(screen.getByText('Create Project')).toBeInTheDocument();
      expect(screen.getByText('Configure Team')).toBeInTheDocument();
      expect(screen.getByText('Start Sprint')).toBeInTheDocument();
      expect(screen.getByText('View Results')).toBeInTheDocument();
    });
  });

  describe('6. Tutorial replay from settings', () => {
    it('should reset and restart tutorial via resetOnboarding + startTutorial', () => {
      // Simulate completed onboarding
      useOnboarding.getState().markFirstRunComplete();
      useOnboarding.getState().completeStep('welcome');
      useOnboarding.getState().completeStep('create-project');

      // Replay tutorial (as settings page does)
      useOnboarding.getState().resetOnboarding();
      useOnboarding.getState().startTutorial();

      const state = useOnboarding.getState();
      expect(state.tutorialActive).toBe(true);
      expect(state.currentStep).toBe('welcome');
      expect(state.completedSteps.size).toBe(0);
      expect(state.isFirstRun).toBe(true);
    });
  });

  describe('7. localStorage persistence', () => {
    it('should persist completed steps to localStorage', () => {
      useOnboarding.getState().startTutorial();
      useOnboarding.getState().completeStep('welcome');
      useOnboarding.getState().exitTutorial();

      const stored = JSON.parse(localStorage.getItem('foundrai-onboarding') || '{}');
      expect(stored.completedSteps).toContain('welcome');
    });

    it('should persist isFirstRun to localStorage', () => {
      useOnboarding.getState().markFirstRunComplete();

      const stored = JSON.parse(localStorage.getItem('foundrai-onboarding') || '{}');
      expect(stored.isFirstRun).toBe(false);
    });
  });

  describe('8. Sample goal integration', () => {
    it('should export sample goal data', async () => {
      const { SAMPLE_WIZARD_STEP1, SAMPLE_PROJECT, isSampleGoal } = await import(
        '@/lib/sample-goals'
      );

      expect(SAMPLE_PROJECT.name).toBe('Hello World API');
      expect(SAMPLE_WIZARD_STEP1).toBeDefined();
      expect(isSampleGoal('Hello World API')).toBe(true);
      expect(isSampleGoal('Custom Project')).toBe(false);
    });
  });

  describe('9. Complete flow integration', () => {
    it('should handle the full onboarding lifecycle', () => {
      // 1. Fresh state: first run detected
      expect(useOnboarding.getState().isFirstRun).toBe(true);

      // 2. User starts tutorial from welcome modal
      useOnboarding.getState().startTutorial();
      expect(useOnboarding.getState().tutorialActive).toBe(true);

      // 3. Progress through all tutorial steps
      const steps = [
        'welcome',
        'create-project',
        'configure-team',
        'start-sprint',
        'view-results',
      ] as const;

      for (const step of steps) {
        expect(useOnboarding.getState().currentStep).toBe(step);
        useOnboarding.getState().completeStep(step);
      }

      // 4. All steps completed
      expect(useOnboarding.getState().completedSteps.size).toBe(5);
      expect(useOnboarding.getState().currentStep).toBe('complete');

      // 5. Exit tutorial
      useOnboarding.getState().exitTutorial();
      expect(useOnboarding.getState().tutorialActive).toBe(false);

      // 6. Mark first run complete
      useOnboarding.getState().markFirstRunComplete();
      expect(useOnboarding.getState().isFirstRun).toBe(false);

      // 7. Verify persistence
      const stored = JSON.parse(localStorage.getItem('foundrai-onboarding') || '{}');
      expect(stored.isFirstRun).toBe(false);
      expect(stored.completedSteps).toHaveLength(5);
    });
  });
});
