import { useState } from 'react';
import { cn } from '@/lib/utils';
import { ChevronUp, ChevronDown, File, Copy, Check } from 'lucide-react';
import type { Artifact } from '@/lib/types';

interface ArtifactDrawerProps {
  artifacts: Artifact[];
}

export function ArtifactDrawer({ artifacts }: ArtifactDrawerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<Artifact | null>(null);
  const [copied, setCopied] = useState(false);

  if (artifacts.length === 0) return null;

  const handleCopy = () => {
    if (selectedFile) {
      navigator.clipboard.writeText(selectedFile.file_path);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className={cn(
      'border-t border-border bg-card transition-all',
      isOpen ? 'h-64' : 'h-10'
    )}>
      {/* Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 w-full px-4 h-10 text-sm text-muted hover:text-foreground"
      >
        {isOpen ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
        <File size={14} />
        <span>Artifacts ({artifacts.length})</span>
      </button>

      {/* Content */}
      {isOpen && (
        <div className="flex h-[calc(100%-2.5rem)] overflow-hidden">
          {/* File list */}
          <div className="w-64 border-r border-border overflow-y-auto">
            {artifacts.map((a) => (
              <button
                key={a.artifact_id}
                onClick={() => setSelectedFile(a)}
                className={cn(
                  'flex items-center gap-2 w-full px-3 py-1.5 text-xs text-left hover:bg-border/50',
                  selectedFile?.artifact_id === a.artifact_id && 'bg-primary/10 text-primary'
                )}
              >
                <File size={12} />
                <span className="truncate font-mono">{a.file_path}</span>
              </button>
            ))}
          </div>

          {/* Preview */}
          <div className="flex-1 overflow-auto">
            {selectedFile ? (
              <div className="p-3">
                <div className="flex items-center justify-between mb-2">
                  <code className="text-xs text-primary font-mono">{selectedFile.file_path}</code>
                  <button onClick={handleCopy} className="text-muted hover:text-foreground">
                    {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
                  </button>
                </div>
                <div className="bg-background rounded-md p-3 font-mono text-xs text-muted">
                  <p>File type: {selectedFile.artifact_type}</p>
                  <p>Size: {selectedFile.size_bytes} bytes</p>
                  <p className="mt-2 text-foreground/50">Content preview requires CodeMirror integration (v0.2.4)</p>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-muted text-xs">
                Select a file to preview
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
