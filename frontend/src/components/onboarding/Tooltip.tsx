import { useState, useRef, useEffect, useCallback, type ReactNode } from 'react';
import { cn } from '@/lib/utils';

type TooltipPosition = 'top' | 'bottom' | 'left' | 'right';

interface TooltipProps {
  /** Content displayed inside the tooltip */
  content: ReactNode;
  /** The element that triggers the tooltip */
  children: ReactNode;
  /** Preferred position of the tooltip relative to the trigger */
  position?: TooltipPosition;
  /** Additional class names for the tooltip container */
  className?: string;
  /** Delay in ms before showing the tooltip */
  delay?: number;
}

const ARROW_STYLES: Record<TooltipPosition, string> = {
  top: 'left-1/2 -translate-x-1/2 top-full border-t-gray-900 dark:border-t-gray-100 border-x-transparent border-b-transparent',
  bottom: 'left-1/2 -translate-x-1/2 bottom-full border-b-gray-900 dark:border-b-gray-100 border-x-transparent border-t-transparent',
  left: 'top-1/2 -translate-y-1/2 left-full border-l-gray-900 dark:border-l-gray-100 border-y-transparent border-r-transparent',
  right: 'top-1/2 -translate-y-1/2 right-full border-r-gray-900 dark:border-r-gray-100 border-y-transparent border-l-transparent',
};

const POSITION_STYLES: Record<TooltipPosition, string> = {
  top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
  bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
  left: 'right-full top-1/2 -translate-y-1/2 mr-2',
  right: 'left-full top-1/2 -translate-y-1/2 ml-2',
};

export function Tooltip({
  content,
  children,
  position = 'top',
  className,
  delay = 200,
}: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const triggerRef = useRef<HTMLDivElement>(null);

  const show = useCallback(() => {
    timeoutRef.current = setTimeout(() => setVisible(true), delay);
  }, [delay]);

  const hide = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setVisible(false);
  }, []);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  return (
    <div
      ref={triggerRef}
      className="relative inline-flex"
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {children}
      {visible && (
        <div
          role="tooltip"
          className={cn(
            'absolute z-50 whitespace-nowrap rounded-md px-3 py-1.5 text-xs font-medium',
            'bg-gray-900 text-gray-50 dark:bg-gray-100 dark:text-gray-900',
            'shadow-md animate-in fade-in-0 zoom-in-95',
            POSITION_STYLES[position],
            className
          )}
        >
          {content}
          <span
            className={cn(
              'absolute border-[5px]',
              ARROW_STYLES[position]
            )}
            aria-hidden="true"
          />
        </div>
      )}
    </div>
  );
}
