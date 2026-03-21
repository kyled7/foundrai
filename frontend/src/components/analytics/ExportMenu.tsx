import { useState, useRef, useEffect } from 'react';
import { Download, FileText, FileImage, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';

interface ExportMenuProps {
  projectId: string;
  className?: string;
}

export function ExportMenu({ projectId, className }: ExportMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  const handleExport = async (format: 'csv' | 'pdf') => {
    setIsOpen(false);
    setIsExporting(true);

    try {
      await api.analytics.exportSprintComparison(projectId, format);
    } catch (error) {
      console.error('Export failed:', error);
      // TODO: Show error toast/notification
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className={cn('relative', className)} ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isExporting}
        className={cn(
          'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
          'bg-primary text-primary-foreground hover:bg-primary/90',
          'disabled:opacity-50 disabled:cursor-not-allowed'
        )}
      >
        <Download size={16} />
        {isExporting ? 'Exporting...' : 'Export'}
        <ChevronDown
          size={16}
          className={cn('transition-transform', isOpen && 'rotate-180')}
        />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-card border border-border rounded-lg shadow-lg z-10">
          <div className="py-1">
            <button
              onClick={() => handleExport('csv')}
              className="w-full flex items-center gap-3 px-4 py-2 text-sm text-foreground hover:bg-accent transition-colors"
            >
              <FileText size={16} className="text-muted" />
              <span>Export as CSV</span>
            </button>
            <button
              onClick={() => handleExport('pdf')}
              className="w-full flex items-center gap-3 px-4 py-2 text-sm text-foreground hover:bg-accent transition-colors"
            >
              <FileImage size={16} className="text-muted" />
              <span>Export as PDF</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
