import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { wizardStep3Schema, type WizardStep3Data } from '@/lib/schemas';
import { useWizard } from '@/stores/wizard';
import { useCreateProject } from '@/hooks/use-projects';
import { AgentAvatar } from '@/components/shared/AgentAvatar';
import { Check } from 'lucide-react';

export function WizardStep3() {
  const { step1Data, step2Data, step3Data, setStep3, setStep, reset } = useWizard();
  const createProject = useCreateProject();

  const { register, handleSubmit, formState: { errors } } = useForm<WizardStep3Data>({
    resolver: zodResolver(wizardStep3Schema),
    defaultValues: step3Data,
  });

  const onSubmit = async (data: WizardStep3Data) => {
    setStep3(data);
    try {
      const project = await createProject.mutateAsync({
        name: step1Data.name,
        description: step1Data.description ?? '',
      });
      reset();
      globalThis.location.assign(`/projects/${project.project_id}`);
    } catch {
      // error state handled by createProject.isError
    }
  };

  const enabledAgents = step2Data.agents.filter(a => a.enabled);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Settings */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-foreground">Sprint Settings</h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs text-muted mb-1">Max Parallel Tasks</label>
            <input
              type="number"
              {...register('maxParallelTasks', { valueAsNumber: true })}
              className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm text-foreground"
            />
            {errors.maxParallelTasks && <p className="text-red-400 text-xs mt-1">{errors.maxParallelTasks.message}</p>}
          </div>

          <div>
            <label className="block text-xs text-muted mb-1">Token Budget</label>
            <input
              type="number"
              {...register('tokenBudget', { valueAsNumber: true })}
              className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm text-foreground"
            />
            {errors.tokenBudget && <p className="text-red-400 text-xs mt-1">{errors.tokenBudget.message}</p>}
          </div>

          <div>
            <label className="block text-xs text-muted mb-1">Sandbox</label>
            <select
              {...register('sandboxProvider')}
              className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm text-foreground"
            >
              <option value="docker">Docker</option>
              <option value="none">None</option>
            </select>
          </div>
        </div>
      </div>

      {/* Review */}
      <div className="space-y-3 border-t border-border pt-4">
        <h3 className="text-sm font-semibold text-foreground">Review</h3>

        <div className="bg-background rounded-lg p-4 space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-muted">Project</span>
            <span className="text-foreground font-medium">{step1Data.name || '—'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted">Directory</span>
            <span className="text-foreground font-mono text-xs">{step1Data.workingDir || '—'}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-muted">Team</span>
            <div className="flex items-center gap-1">
              {enabledAgents.map(a => (
                <AgentAvatar key={a.role} role={a.role.toLowerCase().replace(/([a-z])([A-Z])/g, '$1_$2').toLowerCase()} size="sm" />
              ))}
              <span className="text-foreground text-xs ml-1">{enabledAgents.length} agents</span>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between">
        <button type="button" onClick={() => setStep(2)} className="px-4 py-2 text-sm text-muted hover:text-foreground">
          ← Back
        </button>
        <button
          type="submit"
          disabled={createProject.isPending}
          className="flex items-center gap-2 px-6 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50"
        >
          <Check size={16} />
          {createProject.isPending ? 'Creating...' : 'Create Project'}
        </button>
      </div>

      {createProject.isError && (
        <p className="text-red-400 text-sm">Failed to create project. Please try again.</p>
      )}
    </form>
  );
}
