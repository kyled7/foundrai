import { useRef, useEffect, useState, useCallback } from 'react';

export function useAutoScroll(deps: unknown[]) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  useEffect(() => {
    if (autoScroll) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const el = e.currentTarget;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50;
    setAutoScroll(atBottom);
  }, []);

  const scrollToBottom = useCallback(() => {
    setAutoScroll(true);
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  return { bottomRef, autoScroll, handleScroll, scrollToBottom };
}
