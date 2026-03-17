import { z } from 'zod';

// Step 1: Project basics
export const wizardStep1Schema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name must be 100 characters or less'),
  description: z.string().optional(),
  workingDir: z
    .string()
    .min(1, 'Working directory is required')
    .regex(/^[/~]/, 'Must start with / or ~'),
});

export type WizardStep1Data = z.infer<typeof wizardStep1Schema>;

// Step 2: Team configuration
export const agentSchema = z.object({
  role: z.string().min(1),
  model: z.string().min(1),
  autonomy: z.enum(['low', 'medium', 'high']),
  enabled: z.boolean(),
  customPrompt: z.string().optional(),
});

export type AgentFormData = z.infer<typeof agentSchema>;

export const wizardStep2Schema = z.object({
  agents: z.array(agentSchema).min(1, 'At least one agent is required'),
});

export type WizardStep2Data = z.infer<typeof wizardStep2Schema>;

// Step 3: Settings
export const wizardStep3Schema = z.object({
  maxParallelTasks: z.number().int().min(1).max(10),
  tokenBudget: z.number().int().min(1000),
  sandboxProvider: z.enum(['docker', 'none']),
});

export type WizardStep3Data = z.infer<typeof wizardStep3Schema>;

// Combined schema for full project init
export const projectInitSchema = wizardStep1Schema
  .merge(wizardStep2Schema)
  .merge(wizardStep3Schema);

export type ProjectInitData = z.infer<typeof projectInitSchema>;
