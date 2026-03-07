import { create } from 'zustand';

interface ToastItem {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  duration?: number;
}

interface ToastStore {
  toasts: ToastItem[];
  addToast: (message: string, type?: ToastItem['type'], duration?: number) => void;
  removeToast: (id: string) => void;
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  addToast: (message, type = 'info', duration = 4000) => {
    const id = crypto.randomUUID();
    set((s) => ({ toasts: [...s.toasts, { id, message, type, duration }] }));
    if (duration > 0) {
      setTimeout(() => {
        set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
      }, duration);
    }
  },
  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

const typeStyles: Record<ToastItem['type'], string> = {
  success: 'bg-green-600 text-white',
  error: 'bg-red-600 text-white',
  info: 'bg-blue-600 text-white',
  warning: 'bg-amber-500 text-white',
};

function ToastEntry({ toast }: { toast: ToastItem }) {
  const { removeToast } = useToastStore();
  return (
    <div
      className={`${typeStyles[toast.type]} px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-slide-in min-w-[280px]`}
      role="alert"
      aria-live="assertive"
    >
      <span className="flex-1 text-sm">{toast.message}</span>
      <button
        onClick={() => removeToast(toast.id)}
        className="text-white/80 hover:text-white ml-2"
        aria-label="Dismiss notification"
      >
        ×
      </button>
    </div>
  );
}

export function ToastContainer() {
  const { toasts } = useToastStore();
  if (toasts.length === 0) return null;
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2" aria-label="Notifications">
      {toasts.map((t) => (
        <ToastEntry key={t.id} toast={t} />
      ))}
    </div>
  );
}
