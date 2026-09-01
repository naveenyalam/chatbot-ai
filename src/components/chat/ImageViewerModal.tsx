"use client";

import React, { useEffect } from "react";
import { X, Download, Maximize2, Sparkles } from "lucide-react";

interface ImageViewerModalProps {
  isOpen: boolean;
  imageUrl: string;
  prompt?: string;
  onClose: () => void;
  onDownload: (url: string, filename?: string) => void;
}

export const ImageViewerModal: React.FC<ImageViewerModalProps> = ({
  isOpen,
  imageUrl,
  prompt,
  onClose,
  onDownload,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  if (!isOpen || !imageUrl) return null;

  const filename = prompt
    ? `nova_ai_${prompt.slice(0, 20).replace(/[^a-zA-Z0-9]/g, "_")}.png`
    : "nova_ai_generated_image.png";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-200"
      role="dialog"
      aria-modal="true"
      aria-label="AI Image Viewer"
      onClick={onClose}
    >
      <div
        className="relative max-w-5xl w-full max-h-[90vh] bg-slate-900/90 border border-slate-700/60 rounded-2xl overflow-hidden shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center space-x-2 text-cyan-400 font-medium text-sm">
            <Sparkles className="w-4 h-4" />
            <span>NOVA AI Image Preview</span>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => onDownload(imageUrl, filename)}
              className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-cyan-600/30 hover:bg-cyan-600/50 text-cyan-200 border border-cyan-500/40 text-xs font-medium transition-all shadow-sm active:scale-95"
              title="Download Image"
              aria-label="Download Image"
            >
              <Download className="w-4 h-4" />
              <span>Download</span>
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
              title="Close Viewer"
              aria-label="Close Viewer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Image Preview Canvas */}
        <div className="flex-1 overflow-auto flex items-center justify-center p-6 bg-slate-950/40 min-h-[300px]">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={imageUrl}
            alt={prompt || "NOVA AI Generated Image"}
            className="max-h-[70vh] w-auto max-w-full object-contain rounded-lg shadow-xl border border-slate-800"
          />
        </div>

        {/* Bottom Footer (Prompt Display) */}
        {prompt && (
          <div className="px-6 py-4 border-t border-slate-800 bg-slate-950/80 text-xs text-slate-300 flex items-start space-x-2">
            <span className="font-semibold text-cyan-400 shrink-0">Prompt:</span>
            <p className="line-clamp-2 italic text-slate-200">{prompt}</p>
          </div>
        )}
      </div>
    </div>
  );
};
