import { ProjectWizard } from '@/components/project/ProjectWizard';

export function NewProjectPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-foreground mb-2">Create New Project</h1>
      <p className="text-muted text-sm mb-8">Set up your AI team and start building.</p>
      <ProjectWizard />
    </div>
  );
}
