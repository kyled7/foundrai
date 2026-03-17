import { useWizard } from '@/stores/wizard';
import { WizardStep1 } from './WizardStep1';
import { WizardStep2 } from './WizardStep2';
import { WizardStep3 } from './WizardStep3';
import { cn } from '@/lib/utils';

const steps = [
  { num: 1, label: 'Basics' },
  { num: 2, label: 'Team' },
  { num: 3, label: 'Settings' },
] as const;

export function ProjectWizard() {
  const { step } = useWizard();

  return (
    <div className="max-w-2xl mx-auto">
      {/* Stepper */}
      <div className="flex items-center justify-center gap-4 mb-8">
        {steps.map(({ num, label }, i) => (
          <div key={num} className="flex items-center gap-2">
            <div
              className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium border-2',
                step === num
                  ? 'border-primary bg-primary text-primary-foreground'
                  : step > num
                    ? 'border-primary bg-primary/20 text-primary'
                    : 'border-border text-muted'
              )}
            >
              {step > num ? '✓' : num}
            </div>
            <span className={cn('text-sm', step === num ? 'text-foreground font-medium' : 'text-muted')}>
              {label}
            </span>
            {i < steps.length - 1 && <div className="w-12 h-px bg-border mx-2" />}
          </div>
        ))}
      </div>

      {/* Step content */}
      {step === 1 && <WizardStep1 />}
      {step === 2 && <WizardStep2 />}
      {step === 3 && <WizardStep3 />}
    </div>
  );
}
