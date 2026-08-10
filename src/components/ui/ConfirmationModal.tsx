"use client";

import React, { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, X } from "lucide-react";
import { useApp } from "@/components/providers/ThemeProvider";

interface ConfirmationModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onClose: () => void;
}

export function ConfirmationModal({
  isOpen,
  title,
  message,
  confirmLabel = "Delete",
  cancelLabel = "Cancel",
  onConfirm,
  onClose,
}: ConfirmationModalProps) {
  const { settings } = useApp();
  const animate = settings.animationsEnabled;
  const confirmButtonRef = useRef<HTMLButtonElement>(null);

  // Focus confirm button when modal opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => confirmButtonRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const overlayVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
  };

  const modalVariants = {
    hidden: { opacity: 0, scale: 0.95, y: 10 },
    visible: {
      opacity: 1,
      scale: 1,
      y: 0,
      transition: { type: "spring", duration: 0.3 } as const,
    },
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          role="dialog"
          aria-modal="true"
          aria-labelledby="confirm-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
          initial="hidden"
          animate="visible"
          exit="hidden"
          variants={animate ? overlayVariants : undefined}
          style={!animate ? { opacity: 1 } : {}}
        >
          {/* Modal Container */}
          <motion.div
            className="relative w-full max-w-md bg-surface-primary border border-border-subtle rounded-2xl shadow-2xl overflow-hidden glass-panel"
            variants={animate ? modalVariants : undefined}
            style={!animate ? { scale: 1, y: 0, opacity: 1 } : {}}
          >
            {/* Close Button */}
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-1.5 rounded-lg hover:bg-surface-secondary text-text-muted hover:text-text-primary transition-all"
              aria-label="Close dialog"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Content body */}
            <div className="p-6">
              <div className="flex items-start gap-4">
                {/* Warning icon badge */}
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex-shrink-0">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                
                <div className="flex-grow">
                  <h3
                    id="confirm-modal-title"
                    className="text-base md:text-lg font-bold text-text-primary"
                  >
                    {title}
                  </h3>
                  <p className="text-xs md:text-sm text-text-muted mt-2 leading-relaxed">
                    {message}
                  </p>
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div className="px-6 py-4 bg-surface-secondary/45 border-t border-border-subtle/50 flex items-center justify-end gap-3 select-none">
              <button
                onClick={onClose}
                className="px-4 py-2 text-xs md:text-sm font-semibold text-text-muted hover:text-text-primary rounded-xl hover:bg-surface-secondary transition-all cursor-pointer"
              >
                {cancelLabel}
              </button>
              <button
                ref={confirmButtonRef}
                onClick={() => {
                  onConfirm();
                  onClose();
                }}
                className="px-4 py-2 text-xs md:text-sm font-semibold text-white bg-rose-500 hover:bg-rose-600 rounded-xl shadow-lg shadow-rose-500/15 transition-all cursor-pointer"
              >
                {confirmLabel}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
