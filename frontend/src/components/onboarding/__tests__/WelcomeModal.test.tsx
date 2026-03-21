import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WelcomeModal } from '../WelcomeModal';

// Mock the focus trap hook
vi.mock('../../../hooks/use-focus-trap', () => ({
  useFocusTrap: vi.fn(),
}));

describe('WelcomeModal', () => {
  const mockOnClose = vi.fn();
  const mockOnStartTutorial = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should not render when open is false', () => {
    render(
      <WelcomeModal
        open={false}
        onClose={mockOnClose}
        onStartTutorial={mockOnStartTutorial}
      />
    );

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('should render when open is true', () => {
    render(
      <WelcomeModal
        open={true}
        onClose={mockOnClose}
        onStartTutorial={mockOnStartTutorial}
      />
    );

    expect(screen.getByRole('dialog', { name: /welcome to foundrai/i })).toBeInTheDocument();
  });

  it('should display the welcome title', () => {
    render(
      <WelcomeModal
        open={true}
        onClose={mockOnClose}
        onStartTutorial={mockOnStartTutorial}
      />
    );

    expect(screen.getByText('Welcome to FoundrAI')).toBeInTheDocument();
  });

  it('should display the tagline', () => {
    render(
      <WelcomeModal
        open={true}
        onClose={mockOnClose}
        onStartTutorial={mockOnStartTutorial}
      />
    );

    expect(screen.getByText('Your AI-Powered Founding Team')).toBeInTheDocument();
  });

  it('should display the description', () => {
    render(
      <WelcomeModal
        open={true}
        onClose={mockOnClose}
        onStartTutorial={mockOnStartTutorial}
      />
    );

    expect(screen.getByText(/FoundrAI orchestrates autonomous AI agents/i)).toBeInTheDocument();
  });

  it('should display what you will learn section', () => {
    render(
      <WelcomeModal
        open={true}
        onClose={mockOnClose}
        onStartTutorial={mockOnStartTutorial}
      />
    );

    expect(screen.getByText("What you'll learn:")).toBeInTheDocument();
    expect(screen.getByText(/Setting up your first AI agent team/i)).toBeInTheDocument();
    expect(screen.getByText(/Creating and managing sprints/i)).toBeInTheDocument();
    expect(screen.getByText(/Monitoring agent activity in real-time/i)).toBeInTheDocument();
    expect(screen.getByText(/Configuring API keys and preferences/i)).toBeInTheDocument();
  });

  it('should have a close button', () => {
    render(
      <WelcomeModal
        open={true}
        onClose={mockOnClose}
        onStartTutorial={mockOnStartTutorial}
      />
    );

    const closeButton = screen.getByRole('button', { name: /close/i });
    expect(closeButton).toBeInTheDocument();
  });

  it('should have a skip button', () => {
    render(
      <WelcomeModal
        open={true}
        onClose={mockOnClose}
        onStartTutorial={mockOnStartTutorial}
      />
    );

    const skipButton = screen.getByRole('button', { name: /skip for now/i });
    expect(skipButton).toBeInTheDocument();
  });

  it('should have a start tutorial button', () => {
    render(
      <WelcomeModal
        open={true}
        onClose={mockOnClose}
        onStartTutorial={mockOnStartTutorial}
      />
    );

    const startButton = screen.getByRole('button', { name: /start tutorial/i });
    expect(startButton).toBeInTheDocument();
  });

  it('should call onClose when close button is clicked', () => {
    render(
      <WelcomeModal
        open={true}
        onClose={mockOnClose}
        onStartTutorial={mockOnStartTutorial}
      />
    );

    const closeButton = screen.getByRole('button', { name: /close/i });
    closeButton.click();

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should call onClose when skip button is clicked', () => {
    render(
      <WelcomeModal
        open={true}
        onClose={mockOnClose}
        onStartTutorial={mockOnStartTutorial}
      />
    );

    const skipButton = screen.getByRole('button', { name: /skip for now/i });
    skipButton.click();

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should call onStartTutorial and onClose when start tutorial button is clicked', () => {
    render(
      <WelcomeModal
        open={true}
        onClose={mockOnClose}
        onStartTutorial={mockOnStartTutorial}
      />
    );

    const startButton = screen.getByRole('button', { name: /start tutorial/i });
    startButton.click();

    expect(mockOnStartTutorial).toHaveBeenCalledTimes(1);
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should call onClose when backdrop is clicked', () => {
    const { container } = render(
      <WelcomeModal
        open={true}
        onClose={mockOnClose}
        onStartTutorial={mockOnStartTutorial}
      />
    );

    const backdrop = container.querySelector('.fixed.inset-0');
    expect(backdrop).toBeInTheDocument();

    if (backdrop) {
      backdrop.dispatchEvent(new MouseEvent('click', { bubbles: true }));
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    }
  });

  it('should not call onClose when modal content is clicked', () => {
    render(
      <WelcomeModal
        open={true}
        onClose={mockOnClose}
        onStartTutorial={mockOnStartTutorial}
      />
    );

    const dialog = screen.getByRole('dialog');
    dialog.click();

    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it('should have proper accessibility attributes', () => {
    render(
      <WelcomeModal
        open={true}
        onClose={mockOnClose}
        onStartTutorial={mockOnStartTutorial}
      />
    );

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-label', 'Welcome to FoundrAI');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
  });
});
