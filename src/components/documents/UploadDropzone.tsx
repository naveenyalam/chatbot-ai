"use client";

import React, { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud, FileText, X, AlertCircle } from "lucide-react";
import { uploadDocument, DocumentResponse } from "@/lib/api/documents";

interface UploadDropzoneProps {
  onUploadComplete?: (doc: DocumentResponse) => void;
  onUploadError?: (err: string) => void;
}

export function UploadDropzone({ onUploadComplete, onUploadError }: UploadDropzoneProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [uploadingFile, setUploadingFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const processFile = async (file: File) => {
    // 20MB Max size
    const MAX_SIZE = 20 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
      const err = "File exceeds 20MB maximum size limit.";
      onUploadError?.(err);
      setStatusMsg(err);
      return;
    }

    setUploadingFile(file);
    setUploadProgress(0);
    setStatusMsg("Uploading...");

    try {
      const doc = await uploadDocument(file, (pct) => {
        setUploadProgress(pct);
        if (pct === 100) {
          setStatusMsg("Processing and indexing document...");
        }
      });
      setStatusMsg("Successfully uploaded!");
      onUploadComplete?.(doc);
      setTimeout(() => {
        setUploadingFile(null);
        setUploadProgress(0);
        setStatusMsg("");
      }, 1500);
    } catch (err: any) {
      const errStr = err.message || "Upload failed.";
      onUploadError?.(errStr);
      setStatusMsg(errStr);
      setTimeout(() => {
        setUploadingFile(null);
      }, 3000);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="w-full">
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept=".pdf,.docx,.txt,.md,.csv"
        onChange={handleChange}
        disabled={!!uploadingFile}
      />

      <AnimatePresence mode="wait">
        {!uploadingFile ? (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            onClick={triggerFileInput}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`cursor-pointer border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 relative overflow-hidden flex flex-col items-center justify-center min-h-[180px] ${
              isDragActive
                ? "border-emerald-500 bg-emerald-500/5 shadow-[0_0_20px_rgba(16,185,129,0.1)]"
                : "border-white/10 hover:border-white/20 bg-white/[0.02] hover:bg-white/[0.04]"
            }`}
          >
            {/* Pulsing decoration */}
            {isDragActive && (
              <motion.div
                layoutId="dropzone-glow"
                className="absolute inset-0 bg-emerald-500/10 pointer-events-none blur-xl rounded-full"
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            )}

            <div className="p-3 bg-white/5 rounded-full mb-3 text-white/60">
              <UploadCloud size={28} />
            </div>

            <p className="text-sm font-medium text-white/80 mb-1">
              Drag & drop files here, or <span className="text-emerald-400 font-semibold">browse</span>
            </p>
            <p className="text-xs text-white/40">
              Supports PDF, DOCX, TXT, MD, CSV (Max 20MB)
            </p>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="border border-white/10 bg-white/[0.03] rounded-xl p-6 flex flex-col items-center justify-center min-h-[180px]"
          >
            <div className="flex items-center gap-3 mb-4 w-full max-w-sm p-3 bg-white/5 rounded-lg border border-white/5">
              <div className="p-2 bg-emerald-500/20 text-emerald-400 rounded-md">
                <FileText size={20} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-white truncate">
                  {uploadingFile.name}
                </p>
                <p className="text-[10px] text-white/40">
                  {(uploadingFile.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>
            </div>

            <div className="w-full max-w-sm mb-2">
              <div className="h-1 w-full bg-white/10 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-emerald-500 to-teal-400"
                  initial={{ width: "0%" }}
                  animate={{ width: `${uploadProgress}%` }}
                  transition={{ duration: 0.1 }}
                />
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs font-medium text-white/70">
              {statusMsg.includes("failed") || statusMsg.includes("exceeds") ? (
                <AlertCircle size={14} className="text-rose-400" />
              ) : null}
              <span className={statusMsg.includes("failed") || statusMsg.includes("exceeds") ? "text-rose-400" : ""}>
                {statusMsg}
              </span>
              {uploadProgress < 100 && (
                <span className="text-white/40">({uploadProgress}%)</span>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
