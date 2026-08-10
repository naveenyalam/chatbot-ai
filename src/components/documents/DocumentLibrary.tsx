"use client";

import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  FileText, Search, Trash2, CheckCircle2, Loader2, AlertCircle, 
  X, Check, FolderOpen, MessageSquare
} from "lucide-react";
import { 
  listDocuments, deleteDocument, getDocumentStatus, DocumentResponse 
} from "@/lib/api/documents";
import { UploadDropzone } from "./UploadDropzone";
import { ConfirmationModal } from "@/components/ui/ConfirmationModal";
import { useToast } from "@/components/ui/Toast";

interface DocumentLibraryProps {
  isOpen: boolean;
  onClose: () => void;
  selectedDocIds: string[];
  onToggleSelectDoc: (id: string) => void;
  documents: DocumentResponse[];
  setDocuments: React.Dispatch<React.SetStateAction<DocumentResponse[]>>;
  isWorkspaceView?: boolean;
}

const getFileIcon = (filename: string) => {
  const ext = filename.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "pdf":
      return <span className="text-[9px] font-black tracking-tighter uppercase text-rose-400 bg-rose-500/10 px-1 py-0.5 rounded border border-rose-500/15">PDF</span>;
    case "md":
      return <span className="text-[9px] font-black tracking-tighter uppercase text-sky-400 bg-sky-500/10 px-1 py-0.5 rounded border border-sky-500/15">MD</span>;
    case "txt":
      return <span className="text-[9px] font-black tracking-tighter uppercase text-emerald-400 bg-emerald-500/10 px-1 py-0.5 rounded border border-emerald-500/15">TXT</span>;
    case "doc":
    case "docx":
      return <span className="text-[9px] font-black tracking-tighter uppercase text-blue-400 bg-blue-500/10 px-1 py-0.5 rounded border border-blue-500/15">DOCX</span>;
    default:
      return <FileText size={18} />;
  }
};

export function DocumentLibrary({
  isOpen,
  onClose,
  selectedDocIds,
  onToggleSelectDoc,
  documents,
  setDocuments,
  isWorkspaceView = false,
}: DocumentLibraryProps) {
  const toast = useToast();
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Document deletion modal state
  const [deleteDocId, setDeleteDocId] = useState<string | null>(null);

  const fetchDocs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listDocuments();
      setDocuments(data);
    } catch (err: any) {
      setError(err.message || "Failed to load document catalog.");
    } finally {
      setLoading(false);
    }
  }, [setDocuments]);

  useEffect(() => {
    if (isOpen || isWorkspaceView) {
      fetchDocs();
    }
  }, [isOpen, isWorkspaceView, fetchDocs]);

  useEffect(() => {
    if ((!isOpen && !isWorkspaceView) || documents.length === 0) return;

    const hasTransient = documents.some(
      (d) => d.status === "uploaded" || d.status === "processing"
    );
    if (!hasTransient) return;

    const interval = setInterval(async () => {
      let changed = false;
      const updatedDocs = await Promise.all(
        documents.map(async (doc) => {
          if (doc.status === "uploaded" || doc.status === "processing") {
            try {
              const statusRes = await getDocumentStatus(doc.id);
              if (statusRes.status !== doc.status) {
                changed = true;
                if (statusRes.status === "indexed") {
                  toast.success(`"${doc.original_filename}" indexed and ready`);
                }
                return { ...doc, status: statusRes.status, page_count: statusRes.page_count };
              }
            } catch (err) {
              console.error("Error polling document status:", err);
            }
          }
          return doc;
        })
      );

      if (changed) {
        setDocuments(updatedDocs);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [isOpen, isWorkspaceView, documents, setDocuments, toast]);

  const handleDeleteTrigger = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setDeleteDocId(id);
  };

  const handleConfirmDelete = async () => {
    if (!deleteDocId) return;
    try {
      await deleteDocument(deleteDocId);
      setDocuments((prev) => prev.filter((d) => d.id !== deleteDocId));
      if (selectedDocIds.includes(deleteDocId)) {
        onToggleSelectDoc(deleteDocId);
      }
      toast.success("Document removed from knowledge base");
    } catch (err: any) {
      toast.error(err.message || "Failed to delete document.");
    } finally {
      setDeleteDocId(null);
    }
  };

  const handleUploadComplete = (newDoc: DocumentResponse) => {
    setDocuments((prev) => [newDoc, ...prev]);
    toast.success(`Uploaded "${newDoc.original_filename}"`);
  };

  const filteredDocs = documents.filter((doc) =>
    doc.original_filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "indexed":
      case "ready":
        return <CheckCircle2 size={16} className="text-emerald-400" />;
      case "failed":
        return <AlertCircle size={16} className="text-rose-400" />;
      case "uploaded":
      case "processing":
        return <Loader2 size={16} className="text-amber-400 animate-spin" />;
      default:
        return null;
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (!isOpen && !isWorkspaceView) return null;

  const content = (
    <div className="space-y-6 w-full max-w-5xl mx-auto select-none">
      {/* Header Info */}
      <div className="flex items-center justify-between pb-4 border-b border-border">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-xs font-semibold text-purple-600 dark:text-purple-300">
            <FolderOpen className="w-3.5 h-3.5" /> RAG Knowledge Base Engine
          </div>
          <h1 className="text-3xl font-black text-foreground tracking-tight">
            Knowledge Base & Document Library
          </h1>
          <p className="text-sm text-muted-foreground">
            Ingest PDFs, Word files, or Markdown documents to feed the vector similarity search index.
          </p>
        </div>
        {!isWorkspaceView && (
          <button
            onClick={onClose}
            className="p-2 hover:bg-surface-hover rounded-xl text-muted-foreground hover:text-foreground transition cursor-pointer"
          >
            <X size={20} />
          </button>
        )}
      </div>

      {/* Upload Zone */}
      <UploadDropzone
        onUploadComplete={handleUploadComplete}
        onUploadError={(err) => console.error("Upload error:", err)}
      />

      {/* Filter / Search */}
      <div className="relative">
        <Search className="absolute left-4 top-3.5 text-muted-foreground" size={18} />
        <input
          type="text"
          placeholder="Search document catalog..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full bg-surface border border-border rounded-2xl pl-12 pr-4 py-3.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-indigo-500 transition-all"
        />
      </div>

      {/* Document Listing Grid */}
      {loading && documents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-3">
          <Loader2 size={28} className="animate-spin text-indigo-500 dark:text-indigo-400" />
          <span className="text-xs font-medium">Syncing vector embeddings catalog...</span>
        </div>
      ) : filteredDocs.length === 0 ? (
        <div className="text-center py-16 border border-border rounded-3xl bg-surface glass-panel">
          <FileText className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
          <p className="text-sm font-semibold text-foreground">No documents found matching query</p>
          <p className="text-xs text-muted-foreground mt-1">Upload a PDF or text file to begin semantic RAG index retrieval.</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {filteredDocs.map((doc) => {
            const isSelected = selectedDocIds.includes(doc.id);
            const isReady = doc.status === "indexed";

            return (
              <div
                key={doc.id}
                onClick={() => {
                  if (isReady) {
                    onToggleSelectDoc(doc.id);
                  }
                }}
                className={`flex items-center justify-between p-4.5 rounded-2xl border transition-all duration-200 glass-panel ${
                  !isReady
                    ? "opacity-60 cursor-not-allowed border-border bg-surface/50"
                    : isSelected
                    ? "border-indigo-500/50 bg-indigo-500/10 cursor-pointer shadow-lg shadow-indigo-500/10"
                    : "border-border hover:border-indigo-500/30 hover:bg-surface-hover cursor-pointer"
                }`}
              >
                <div className="flex items-center gap-3.5 min-w-0">
                  {isReady && (
                    <div
                      className={`w-5 h-5 rounded-lg flex items-center justify-center border transition-all ${
                        isSelected
                          ? "bg-indigo-600 border-indigo-600 text-white"
                          : "border-border bg-surface"
                      }`}
                    >
                      {isSelected && <Check size={12} strokeWidth={3} />}
                    </div>
                  )}

                  <div className="w-10 h-10 bg-indigo-500/10 text-indigo-500 dark:text-indigo-400 rounded-xl border border-indigo-500/20 flex items-center justify-center flex-shrink-0">
                    {getFileIcon(doc.original_filename)}
                  </div>

                  <div className="min-w-0">
                    <p className="text-sm font-bold text-foreground truncate max-w-[360px]">
                      {doc.original_filename}
                    </p>
                    <p className="text-xs text-muted-foreground flex items-center gap-2 mt-1">
                      <span>{formatSize(doc.file_size)}</span>
                      {doc.page_count > 0 && (
                        <>
                          <span>•</span>
                          <span>{doc.page_count} pages</span>
                        </>
                      )}
                      <span>•</span>
                      <span className="capitalize font-semibold text-indigo-500 dark:text-indigo-400">{doc.status}</span>
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {getStatusIcon(doc.status)}
                  {isReady && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (!selectedDocIds.includes(doc.id)) {
                          onToggleSelectDoc(doc.id);
                        }
                        onClose();
                      }}
                      className="flex items-center gap-1 px-2.5 py-1 rounded-xl bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-400 border border-indigo-500/20 text-xs font-semibold transition-all cursor-pointer"
                      title="Ask NOVA about this document"
                    >
                      <MessageSquare size={13} />
                      <span className="hidden sm:inline">Ask NOVA</span>
                    </button>
                  )}
                  <button
                    onClick={(e) => handleDeleteTrigger(e, doc.id)}
                    className="p-2 hover:bg-rose-500/10 text-muted-foreground hover:text-rose-400 rounded-xl transition-colors cursor-pointer"
                    title="Delete document"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Confirmation modal for doc delete */}
      <ConfirmationModal
        isOpen={Boolean(deleteDocId)}
        title="Delete Document"
        message="Are you sure you want to delete this document from your knowledge base? All extracted chunks will be permanently removed."
        confirmLabel="Delete Document"
        onConfirm={handleConfirmDelete}
        onClose={() => setDeleteDocId(null)}
      />

      {/* Footer */}
      <div className="p-4 rounded-2xl bg-surface border border-border glass-panel flex items-center justify-between">
        <span className="text-xs text-muted-foreground font-medium">
          <strong className="text-foreground">{selectedDocIds.length}</strong> document(s) active in prompt context
        </span>
        {!isWorkspaceView && (
          <button
            onClick={onClose}
            className="px-5 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold rounded-xl text-xs shadow-lg hover:from-indigo-500 hover:to-purple-500 transition cursor-pointer"
          >
            Apply Context
          </button>
        )}
      </div>
    </div>
  );

  if (isWorkspaceView) {
    return <div className="flex-1 overflow-y-auto p-6 md:p-10">{content}</div>;
  }

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          className="relative w-full max-w-3xl bg-surface-elevated border border-border rounded-3xl p-6 overflow-hidden shadow-2xl flex flex-col max-h-[85vh] glass-panel"
        >
          {content}
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
