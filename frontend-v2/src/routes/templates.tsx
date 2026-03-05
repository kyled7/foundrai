import { useState } from 'react';
import { useTemplates } from '@/hooks/use-analytics';
import { AgentAvatar } from '@/components/shared/AgentAvatar';
import { EmptyState } from '@/components/shared/EmptyState';
import { PageSkeleton } from '@/components/shared/LoadingSkeleton';
import { cn } from '@/lib/utils';
import { Search, X, Users, ArrowRight } from 'lucide-react';
import type { TeamTemplate } from '@/lib/types';

export function TemplatesPage() {
  const { data: templates, isLoading } = useTemplates();
  const [search, setSearch] = useState('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [previewTemplate, setPreviewTemplate] = useState<TeamTemplate | null>(null);

  if (isLoading) return <PageSkeleton />;

  const allTemplates = templates ?? [];
  const allTags = [...new Set(allTemplates.flatMap((t) => t.tags))];

  const filtered = allTemplates.filter((t) => {
    const matchesSearch = !search || t.name.toLowerCase().includes(search.toLowerCase()) || t.description.toLowerCase().includes(search.toLowerCase());
    const matchesTag = !selectedTag || t.tags.includes(selectedTag);
    return matchesSearch && matchesTag;
  });

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-foreground">Templates</h1>

      {/* Search & Filter */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search templates..."
            className="w-full pl-9 pr-3 py-2 bg-background border border-border rounded-md text-sm text-foreground placeholder:text-muted"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {allTags.map((tag) => (
            <button
              key={tag}
              onClick={() => setSelectedTag(selectedTag === tag ? null : tag)}
              className={cn(
                'px-3 py-1.5 rounded-full text-xs border transition-colors',
                selectedTag === tag ? 'border-primary bg-primary/10 text-primary' : 'border-border text-muted hover:text-foreground'
              )}
            >
              {tag}
            </button>
          ))}
        </div>
      </div>

      {/* Grid */}
      {filtered.length === 0 ? (
        <EmptyState title="No templates found" description={search ? 'Try a different search term.' : 'No templates available yet.'} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((t) => (
            <div
              key={t.id}
              onClick={() => setPreviewTemplate(t)}
              className="bg-card border border-border rounded-lg p-4 cursor-pointer hover:border-primary/50 transition-colors"
            >
              <h3 className="font-semibold text-foreground">{t.name}</h3>
              <p className="text-muted text-sm mt-1 line-clamp-2">{t.description}</p>
              <div className="flex items-center gap-2 mt-3">
                <Users size={14} className="text-muted" />
                <span className="text-muted text-xs">{t.agents.length} agents</span>
                <div className="flex -space-x-1 ml-auto">
                  {t.agents.slice(0, 4).map((a) => (
                    <AgentAvatar key={a.role} role={a.role} size="sm" />
                  ))}
                </div>
              </div>
              {t.tags.length > 0 && (
                <div className="flex gap-1 mt-2">
                  {t.tags.map((tag) => (
                    <span key={tag} className="text-xs px-2 py-0.5 bg-border rounded-full text-muted">{tag}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Preview Modal */}
      {previewTemplate && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4" onClick={() => setPreviewTemplate(null)}>
          <div className="bg-card border border-border rounded-xl max-w-lg w-full p-6 space-y-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-xl font-bold text-foreground">{previewTemplate.name}</h2>
                <p className="text-muted text-sm mt-1">{previewTemplate.description}</p>
              </div>
              <button onClick={() => setPreviewTemplate(null)} className="text-muted hover:text-foreground">
                <X size={20} />
              </button>
            </div>

            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-foreground">Team ({previewTemplate.agents.length} agents)</h3>
              {previewTemplate.agents.map((a) => (
                <div key={a.role} className="flex items-center gap-3 bg-background rounded-md p-3">
                  <AgentAvatar role={a.role} size="sm" />
                  <div>
                    <p className="text-foreground text-sm capitalize">{a.role.replace('_', ' ')}</p>
                    <p className="text-muted text-xs">{a.model} · {a.autonomy}</p>
                  </div>
                </div>
              ))}
            </div>

            <a
              href={`/projects/new?template=${previewTemplate.id}`}
              className="flex items-center justify-center gap-2 w-full px-4 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90"
            >
              Use This Template
              <ArrowRight size={16} />
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
