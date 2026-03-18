import { ChevronRight } from 'lucide-react';
import type { BreadcrumbItem } from '@/lib/types';

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
}

export function Breadcrumbs({ items }: BreadcrumbsProps) {
  if (items.length === 0) return null;

  return (
    <nav aria-label="Breadcrumb">
      <ol className="flex items-center gap-1 text-sm">
        {items.map((item, i) => {
          const isLast = i === items.length - 1;
          return (
            <li key={i} className="flex items-center gap-1">
              {i > 0 && <ChevronRight size={14} className="text-muted shrink-0" />}
              {item.href && !isLast ? (
                <a href={item.href} className="text-muted hover:text-foreground transition-colors">
                  {item.label}
                </a>
              ) : (
                <span className="text-foreground font-medium" aria-current={isLast ? 'page' : undefined}>
                  {item.label}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
