import { useState } from 'react';

interface Props {
  context: Record<string, unknown>;
  actionType: string;
}

function CollapsibleSection({
  title,
  children,
  defaultOpen = false,
  icon
}: {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  icon?: string;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded mt-2">
      <button
        onClick={() => setOpen(!open)}
        className="w-full text-left px-3 py-2 text-sm font-medium bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-t flex justify-between items-center"
      >
        <span>{icon && `${icon} `}{title}</span>
        <span>{open ? '▼' : '▶'}</span>
      </button>
      {open && (
        <div className="p-3 text-xs overflow-x-auto">
          {children}
        </div>
      )}
    </div>
  );
}

function CodeBlock({ code, language = 'text' }: { code: string; language?: string }) {
  return (
    <pre className="whitespace-pre-wrap bg-white dark:bg-gray-950 p-3 rounded font-mono text-xs border border-gray-200 dark:border-gray-700 overflow-x-auto">
      <code className={`language-${language}`}>{code}</code>
    </pre>
  );
}

function DiffView({ diff }: { diff: string }) {
  const lines = diff.split('\n');
  return (
    <pre className="whitespace-pre-wrap bg-white dark:bg-gray-950 p-3 rounded font-mono text-xs border border-gray-200 dark:border-gray-700 overflow-x-auto">
      {lines.map((line, idx) => {
        let className = '';
        if (line.startsWith('+')) {
          className = 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-950/30';
        } else if (line.startsWith('-')) {
          className = 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30';
        } else if (line.startsWith('@@')) {
          className = 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/30 font-semibold';
        }
        return (
          <div key={idx} className={className}>
            {line}
          </div>
        );
      })}
    </pre>
  );
}

function renderValue(key: string, value: unknown): React.ReactNode {
  // Code content
  if (typeof value === 'string' && (
    key.toLowerCase().includes('code') ||
    key.toLowerCase().includes('content') ||
    key.toLowerCase().includes('file_content') ||
    key.toLowerCase().includes('body')
  ) && value.length > 50) {
    return <CodeBlock code={value} />;
  }

  // Diff content
  if (typeof value === 'string' && (
    key.toLowerCase().includes('diff') ||
    key.toLowerCase().includes('patch') ||
    value.startsWith('diff --git') ||
    value.includes('\n+++') ||
    value.includes('\n---')
  )) {
    return <DiffView diff={value} />;
  }

  // File paths
  if (typeof value === 'string' && (
    key.toLowerCase().includes('path') ||
    key.toLowerCase().includes('file')
  )) {
    return (
      <span className="text-blue-600 dark:text-blue-400 font-mono break-all">
        {value}
      </span>
    );
  }

  // URLs
  if (typeof value === 'string' && (value.startsWith('http://') || value.startsWith('https://'))) {
    return (
      <a
        href={value}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-600 dark:text-blue-400 hover:underline break-all"
      >
        {value}
      </a>
    );
  }

  // Arrays and objects
  if (typeof value === 'object' && value !== null) {
    return (
      <pre className="whitespace-pre-wrap bg-white dark:bg-gray-950 p-2 rounded font-mono overflow-x-auto">
        {JSON.stringify(value, null, 2)}
      </pre>
    );
  }

  // Simple strings
  if (typeof value === 'string') {
    return <span className="break-words">{value}</span>;
  }

  // Numbers, booleans, etc.
  return <span className="font-mono">{String(value)}</span>;
}

export function ContextRenderer({ context, actionType }: Props) {
  const contextEntries = Object.entries(context);

  if (contextEntries.length === 0) {
    return (
      <div className="text-xs text-gray-400 italic py-2">
        No additional context provided
      </div>
    );
  }

  // Determine icon based on action type
  const getIcon = () => {
    if (actionType.includes('commit') || actionType.includes('git')) return '🔀';
    if (actionType.includes('code') || actionType.includes('file')) return '📝';
    if (actionType.includes('deploy') || actionType.includes('release')) return '🚀';
    if (actionType.includes('delete') || actionType.includes('remove')) return '🗑️';
    if (actionType.includes('create') || actionType.includes('add')) return '➕';
    if (actionType.includes('update') || actionType.includes('modify')) return '✏️';
    return '📋';
  };

  // Check if all entries are simple (non-code, non-diff)
  const hasComplexContent = contextEntries.some(([key, value]) => {
    if (typeof value !== 'string') return true;
    if (key.toLowerCase().includes('code')) return true;
    if (key.toLowerCase().includes('diff')) return true;
    if (key.toLowerCase().includes('content') && value.length > 100) return true;
    return false;
  });

  // Simple context - show inline
  if (!hasComplexContent && contextEntries.length <= 3) {
    return (
      <div className="mt-2 bg-white dark:bg-gray-900 rounded p-3 border border-gray-200 dark:border-gray-700 space-y-2">
        {contextEntries.map(([key, value]) => (
          <div key={key}>
            <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
              {key}:
            </span>
            <div className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
              {renderValue(key, value)}
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Complex context - use collapsible sections
  return (
    <div className="mt-2">
      {contextEntries.map(([key, value]) => (
        <CollapsibleSection
          key={key}
          title={key}
          icon={getIcon()}
          defaultOpen={contextEntries.length === 1}
        >
          {renderValue(key, value)}
        </CollapsibleSection>
      ))}
    </div>
  );
}
