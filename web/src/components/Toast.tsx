import { useCallback, useRef, useState } from 'react';

interface Toast {
  id: string;
  message: string;
  onUndo?: () => void;
  onExpire?: () => void;
}

interface ToastContextValue {
  toasts: Toast[];
  showToast: (message: string, onUndo?: () => void, onExpire?: () => void) => void;
  dismissToast: (id: string, wasUndo?: boolean) => void;
}

let toastIdCounter = 0;

export function useToast(): ToastContextValue {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const toastMapRef = useRef<Map<string, Toast>>(new Map());

  const dismissToast = useCallback((id: string, wasUndo: boolean = false) => {
    const toast = toastMapRef.current.get(id);
    // If dismissed without undo (timeout or X button), call onExpire
    if (toast && !wasUndo && toast.onExpire) {
      toast.onExpire();
    }
    toastMapRef.current.delete(id);
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback((message: string, onUndo?: () => void, onExpire?: () => void) => {
    const id = `toast-${++toastIdCounter}`;
    const toast = { id, message, onUndo, onExpire };
    toastMapRef.current.set(id, toast);
    setToasts((prev) => [...prev, toast]);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      dismissToast(id, false);
    }, 5000);
  }, [dismissToast]);

  return { toasts, showToast, dismissToast };
}

interface ToastContainerProps {
  toasts: Toast[];
  onDismiss: (id: string, wasUndo?: boolean) => void;
}

export function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

interface ToastItemProps {
  toast: Toast;
  onDismiss: (id: string, wasUndo?: boolean) => void;
}

function ToastItem({ toast, onDismiss }: ToastItemProps) {
  const [isExiting, setIsExiting] = useState(false);

  const handleDismiss = useCallback((wasUndo: boolean = false) => {
    setIsExiting(true);
    setTimeout(() => onDismiss(toast.id, wasUndo), 200);
  }, [onDismiss, toast.id]);

  const handleUndo = useCallback(() => {
    if (toast.onUndo) {
      toast.onUndo();
    }
    handleDismiss(true);
  }, [toast, handleDismiss]);

  return (
    <div
      className={`flex items-center gap-3 rounded-lg bg-slate-800 px-4 py-3 text-sm text-white shadow-lg transition-all duration-200 ${
        isExiting ? 'translate-x-full opacity-0' : 'translate-x-0 opacity-100'
      }`}
      role="alert"
    >
      <span>{toast.message}</span>
      {toast.onUndo && (
        <button
          type="button"
          onClick={handleUndo}
          className="font-semibold text-blue-400 hover:text-blue-300"
        >
          Undo
        </button>
      )}
      <button
        type="button"
        onClick={() => handleDismiss(false)}
        className="ml-2 text-slate-400 hover:text-white"
        aria-label="Dismiss"
      >
        <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}
