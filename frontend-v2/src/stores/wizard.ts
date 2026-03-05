import { create } from 'zustand';
import type { WizardStep1Data, WizardStep2Data, WizardStep3Data, AgentFormData } from '@/lib/schemas';
import type { TeamTemplate } from '@/lib/types';

export const DEFAULT_AGENTS: AgentFormData[] = [
  { role: 'ProductManager', model: 'claude-sonnet-4', autonomy: 'medium', enabled: true },
  { role: 'Developer', model: 'claude-sonnet-4', autonomy: 'medium', enabled: true },
  { role: 'QAEngineer', model: 'claude-sonnet-4', autonomy: 'medium', enabled: true },
  { role: 'Architect', model: 'claude-sonnet-4', autonomy: 'low', enabled: false },
  { role: 'Designer', model: 'claude-sonnet-4', autonomy: 'low', enabled: false },
];

interface WizardState {
  step: 1 | 2 | 3;
  step1Data: WizardStep1Data;
  step2Data: WizardStep2Data;
  step3Data: WizardStep3Data;
  templateId: string | null;

  setStep: (step: 1 | 2 | 3) => void;
  setStep1: (data: WizardStep1Data) => void;
  setStep2: (data: WizardStep2Data) => void;
  setStep3: (data: WizardStep3Data) => void;
  applyTemplate: (template: TeamTemplate) => void;
  reset: () => void;
}

const initialState = {
  step: 1 as const,
  step1Data: { name: '', description: '', workingDir: '' },
  step2Data: { agents: DEFAULT_AGENTS },
  step3Data: { maxParallelTasks: 3, tokenBudget: 100000, sandboxProvider: 'docker' as const },
  templateId: null,
};

export const useWizard = create<WizardState>((set) => ({
  ...initialState,

  setStep: (step) => set({ step }),
  setStep1: (step1Data) => set({ step1Data }),
  setStep2: (step2Data) => set({ step2Data }),
  setStep3: (step3Data) => set({ step3Data }),

  applyTemplate: (template) =>
    set({
      templateId: template.id,
      step2Data: {
        agents: template.agents.map((a) => ({
          role: a.role,
          model: a.model,
          autonomy: a.autonomy,
          enabled: true,
          customPrompt: a.system_prompt,
        })),
      },
    }),

  reset: () => set(initialState),
}));
