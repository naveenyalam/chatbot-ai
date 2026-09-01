"use client";

import React, { useState } from "react";
import { Sparkles, Download, Maximize2, Image as ImageIcon, AlertCircle, RefreshCw } from "lucide-react";

interface ImageMessageProps {
  imageUrl?: string;
  prompt?: string;
  isLoading?: boolean;
  error?: string;
  onOpenModal?: (url: string, prompt?: string) => void;
  onDownload?: (url: string, filename?: string) => void;
}

export const ImageMessage: React.FC<ImageMessageProps> = ({
  imageUrl,
  prompt,
  isLoading = false,
  error,
  onOpenModal,
  onDownload,
}) => {
  const [imageError, setImageError] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);

  const filename = prompt
    ? `nova_ai_${prompt.slice(0, 20).replace(/[^a-zA-Z0-9]/g, "_")}.png`
    : "nova_ai_image.png";

  if (isLoading) {
    return (
      <div className="my-3 p-4 rounded-xl border border-cyan-500/30 bg-slate-900/60 backdrop-blur-md shadow-lg max-w-md w-full animate-pulse">
        <div className="flex items-center space-x-2 text-cyan-400 text-xs font-semibold mb-3">
          <Sparkles className="w-4 h-4 animate-spin text-cyan-400" />
          <span>NOVA AI is generating image...</span>
        </div>
        <div className="w-full h-64 bg-slate-800/80 rounded-lg flex flex-col items-center justify-center space-y-2 border border-slate-700/50">
          <ImageIcon className="w-10 h-10 text-cyan-500/40 animate-bounce" />
          <span className="text-xs text-slate-400">Rendering AI artwork...</span>
        </div>
        {prompt && (
          <p className="mt-3 text-xs text-slate-400 italic line-clamp-1">
            &quot;{prompt}&quot;
          </p>
        )}
      </div>
    );
  }

  if (error || imageError) {
    return (
      <div className="my-3 p-4 rounded-xl border border-rose-500/30 bg-rose-950/20 backdrop-blur-md shadow-lg max-w-md w-full">
        <div className="flex items-center space-x-2 text-rose-400 text-xs font-semibold mb-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>Image Generation Failed</span>
        </div>
        <p className="text-xs text-slate-300">
          {error || "Unable to load the generated image. The URL may have expired or network failed."}
        </p>
      </div>
    );
  }

  if (!imageUrl) return null;

  return (
    <div className="my-3 max-w-md w-full group relative rounded-xl border border-slate-800 bg-slate-900/70 backdrop-blur-md shadow-xl overflow-hidden transition-all hover:border-cyan-500/40">
      {/* Header Prompt Tag */}
      {prompt && (
        <div className="px-4 py-2 bg-slate-950/60 border-b border-slate-800 flex items-center space-x-2 text-xs text-slate-300">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
          <span className="truncate font-medium italic text-slate-200" title={prompt}>
            {prompt}
          </span>
        </div>
      )}

      {/* Image Container with Hover Controls */}
      <div className="relative w-full aspect-square bg-slate-950 flex items-center justify-center overflow-hidden">
        {!isLoaded && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-900 animate-pulse">
            <RefreshCw className="w-6 h-6 text-cyan-400 animate-spin" />
          </div>
        )}

        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={imageUrl}
          alt={prompt || "NOVA AI Generated Image"}
          onLoad={() => setIsLoaded(true)}
          onError={() => setImageError(true)}
          className={`w-full h-full object-cover transition-transform duration-300 group-hover:scale-105 ${
            isLoaded ? "opacity-100" : "opacity-0"
          }`}
        />

        {/* Action Overlay */}
        <div className="absolute inset-0 bg-slate-950/60 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center space-x-3 backdrop-blur-[2px]">
          <button
            onClick={() => onOpenModal?.(imageUrl, prompt)}
            className="p-2.5 rounded-full bg-cyan-600/80 hover:bg-cyan-500 text-white shadow-lg transition-transform active:scale-95"
            title="Expand Image"
            aria-label="Expand Image"
          >
            <Maximize2 className="w-5 h-5" />
          </button>

          <button
            onClick={() => onDownload?.(imageUrl, filename)}
            className="p-2.5 rounded-full bg-slate-800/90 hover:bg-slate-700 text-white border border-slate-600 shadow-lg transition-transform active:scale-95"
            title="Download Image"
            aria-label="Download Image"
          >
            <Download className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};
