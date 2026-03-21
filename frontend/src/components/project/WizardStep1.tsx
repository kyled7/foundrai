import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { wizardStep1Schema, type WizardStep1Data } from '@/lib/schemas';
import { useWizard } from '@/stores/wizard';
import { useOnboarding } from '@/stores/onboarding';
import { useTemplates } from '@/hooks/use-analytics';
import { SAMPLE_WIZARD_STEP1 } from '@/lib/sample-goals';

export function WizardStep1() {
  const { step1Data, setStep1, setStep, applyTemplate, applySampleGoal } = useWizard();
  const { tutorialActive } = useOnboarding();
  const { data: templates } = useTemplates();

  const { register, handleSubmit, reset, formState: { errors } } = useForm<WizardStep1Data>({
    resolver: zodResolver(wizardStep1Schema),
    defaultValues: step1Data,
  });

  useEffect(() => {
    if (tutorialActive && !step1Data.name) {
      applySampleGoal();
      reset(SAMPLE_WIZARD_STEP1);
    }
  }, [tutorialActive, step1Data.name, applySampleGoal, reset]);

  const onSubmit = (data: WizardStep1Data) => {
    setStep1(data);
    setStep(2);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      {tutorialActive && (
        <div className="bg-primary/10 border border-primary/30 rounded-lg px-4 py-3 text-sm text-foreground">
          <p className="font-medium">Sample project pre-filled!</p>
          <p className="text-muted mt-1">
            We&apos;ve set up a &quot;Hello World API&quot; project for you. Feel free to customize it or continue with the defaults.
          </p>
        </div>
      )}
      <div>
        <label className="block text-sm font-medium text-foreground mb-1">Project Name *</label>
        <input
          {...register('name')}
          placeholder="My Awesome Project"
          className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-primary/50"
        />
        {errors.name && <p className="text-red-400 text-xs mt-1">{errors.name.message}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground mb-1">Description</label>
        <textarea
          {...register('description')}
          rows={3}
          placeholder="What does this project do?"
          className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted resize-none focus:outline-none focus:ring-2 focus:ring-primary/50"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground mb-1">Working Directory *</label>
        <input
          {...register('workingDir')}
          placeholder="~/projects/my-app"
          className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm text-foreground font-mono placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-primary/50"
        />
        {errors.workingDir && <p className="text-red-400 text-xs mt-1">{errors.workingDir.message}</p>}
      </div>

      {/* Template quick-start */}
      {templates && templates.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-foreground mb-1">Quick Start from Template</label>
          <select
            onChange={(e) => {
              const t = templates.find((t) => t.id === e.target.value);
              if (t) applyTemplate(t);
            }}
            className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm text-foreground"
            defaultValue=""
          >
            <option value="" disabled>Select a template (optional)</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>{t.name} — {t.agents.length} agents</option>
            ))}
          </select>
        </div>
      )}

      <div className="flex justify-end">
        <button
          type="submit"
          className="px-6 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90"
        >
          Next →
        </button>
      </div>
    </form>
  );
}
