"use client";

import React, { useState, useEffect } from "react";
import { Bookmark, Search, Trash2, Copy, Check, Loader2, Star } from "lucide-react";
import { ConfirmationModal } from "@/components/ui/ConfirmationModal";
import { listSavedResponses, deleteSavedResponse, SavedResponseItem } from "@/lib/api/workspace";
import { useToast } from "@/components/ui/Toast";

export function SavedResponses() {
  const toast = useToast();
  const [responses, setResponses] = useState<SavedResponseItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  const fetchResponses = async () => {
    try {
      setIsLoading(true);
      const data = await listSavedResponses();
      setResponses(data);
    } catch (err: any) {
      toast.error(err.message || "Failed to load saved responses.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchResponses();
  }, []);

  const handleConfirmDelete = async () => {
    if (!deleteTargetId) return;
    try {
      await deleteSavedResponse(deleteTargetId);
      setResponses((prev) => prev.filter((r) => r.id !== deleteTargetId));
      toast.success("Saved response deleted.");
    } catch (err: any) {
      toast.error(err.message || "Failed to delete saved response.");
    } finally {
      setDeleteTargetId(null);
    }
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filtered = responses.filter(
    (r) => r.title.toLowerCase().includes(searchQuery.toLowerCase()) || r.content.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex-1 p-6 md:p-8 max-w-6xl mx-auto w-full space-y-6 overflow-y-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-pink-500/10 border border-pink-500/20 text-pink-400">
            <Bookmark className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-foreground">Saved AI Responses</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Access your bookmarked AI answers, code snippets, and synthesized insights.
            </p>
          </div>
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search saved responses..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full py-2 pl-8 pr-3 rounded-xl bg-surface border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-pink-500"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="py-16 text-center text-muted-foreground flex flex-col items-center gap-2">
          <Loader2 className="w-6 h-6 animate-spin text-pink-400" />
          <span className="text-xs">Loading saved responses...</span>
        </div>
      ) : filtered.length > 0 ? (
        <div className="space-y-4">
          {filtered.map((item) => (
            <div key={item.id} className="p-5 rounded-2xl bg-surface border border-border glass-panel space-y-3 group">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-foreground group-hover:text-pink-400 transition-colors">{item.title}</h3>
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => handleCopy(item.id, item.content)}
                    className="p-1.5 rounded-lg border border-border bg-surface hover:bg-surface-hover text-muted-foreground hover:text-foreground transition-all cursor-pointer"
                  >
                    {copiedId === item.id ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-pink-400" />}
                  </button>
                  <button
                    onClick={() => setDeleteTargetId(item.id)}
                    className="p-1.5 rounded-lg hover:bg-red-500/10 text-muted-foreground hover:text-red-400 transition-colors cursor-pointer"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
              <p className="text-xs font-sans text-muted-foreground/90 leading-relaxed bg-surface/50 p-3 rounded-xl border border-border/50 whitespace-pre-wrap">
                {item.content}
              </p>
              <div className="text-[10px] text-muted-foreground/60 font-mono">
                Saved {item.created_at ? new Date(item.created_at).toLocaleDateString() : "recently"}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-12 px-6 rounded-2xl bg-surface/50 border border-border text-center space-y-3">
          <Bookmark className="w-8 h-8 text-pink-400 mx-auto" />
          <h3 className="text-sm font-bold text-foreground">No saved responses yet</h3>
          <p className="text-xs text-muted-foreground">Bookmark important AI answers directly from the chat interface.</p>
        </div>
      )}

      <ConfirmationModal
        isOpen={Boolean(deleteTargetId)}
        title="Delete Saved Response"
        message="Are you sure you want to delete this saved response? It will be removed permanently from your productivity workspace."
        confirmLabel="Delete"
        cancelLabel="Cancel"
        onConfirm={handleConfirmDelete}
        onClose={() => setDeleteTargetId(null)}
      />
    </div>
  );
}
