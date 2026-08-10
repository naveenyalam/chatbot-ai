"use client";

import React, { createContext, useContext, useState, useCallback, useMemo, ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from "lucide-react";
import { cn } from "@/lib/utils";

export type ToastType = "success" | "error" | "info" | "warning";

export interface ToastItem {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

interface ToastContextValue {
  showToast: (message: string, type?: ToastType, duration?: number) => void;
  success: (message: string, duration?: number) => void;
  error: (message: string, duration?: number) => void;
  info: (message: string, duration?: number) => void;
  warning: (message: string, duration?: number) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (message: string, type: ToastType = "info", duration = 4000) => {
      const id = Math.random().toString(36).substring(7);
      const newToast: ToastItem = { id, type, message, duration };

      setToasts((prev) => [...prev.slice(-4), newToast]); // Limit to max 5 toasts

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
    },
    [removeToast]
  );

  const success = useCallback(
    (message: string, duration?: number) => showToast(message, "success", duration),
    [showToast]
  );
  const error = useCallback(
    (message: string, duration?: number) => showToast(message, "error", duration),
    [showToast]
  );
  const info = useCallback(
    (message: string, duration?: number) => showToast(message, "info", duration),
    [showToast]
  );
  const warning = useCallback(
    (message: string, duration?: number) => showToast(message, "warning", duration),
    [showToast]
  );

  const contextValue = useMemo(
    () => ({ showToast, success, error, info, warning }),
    [showToast, success, error, info, warning]
  );

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      {/* Toast Render Container */}
      <div
        aria-live="polite"
        aria-atomic="true"
        className="fixed bottom-6 right-6 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none select-none px-4 sm:px-0"
      >
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
              className={cn(
                "pointer-events-auto flex items-center justify-between p-3.5 rounded-2xl border shadow-xl backdrop-blur-xl text-xs md:text-sm font-medium transition-all glass-panel",
                toast.type === "success" &&
                  "bg-emerald-50 dark:bg-emerald-950/90 border-emerald-200 dark:border-emerald-500/30 text-emerald-900 dark:text-emerald-200",
                toast.type === "error" &&
                  "bg-rose-50 dark:bg-rose-950/90 border-rose-200 dark:border-rose-500/30 text-rose-900 dark:text-rose-200",
                toast.type === "warning" &&
                  "bg-amber-50 dark:bg-amber-950/90 border-amber-200 dark:border-amber-500/30 text-amber-900 dark:text-amber-200",
                toast.type === "info" &&
                  "bg-indigo-50 dark:bg-indigo-950/90 border-indigo-200 dark:border-indigo-500/30 text-indigo-900 dark:text-indigo-200"
              )}
            >
              <div className="flex items-center gap-3 min-w-0 pr-2">
                {toast.type === "success" && <CheckCircle2 className="w-4.5 h-4.5 text-emerald-400 flex-shrink-0" />}
                {toast.type === "error" && <AlertCircle className="w-4.5 h-4.5 text-rose-400 flex-shrink-0" />}
                {toast.type === "warning" && <AlertTriangle className="w-4.5 h-4.5 text-amber-400 flex-shrink-0" />}
                {toast.type === "info" && <Info className="w-4.5 h-4.5 text-indigo-400 flex-shrink-0" />}
                <span className="truncate leading-tight">{toast.message}</span>
              </div>
              <button
                onClick={() => removeToast(toast.id)}
                className="p-1 rounded-lg hover:bg-black/5 dark:hover:bg-white/10 opacity-70 hover:opacity-100 transition-opacity cursor-pointer"
                aria-label="Dismiss toast"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}
