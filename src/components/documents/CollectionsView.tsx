"use client";

import React, { useState, useEffect } from "react";
import { FolderKanban, Plus, Trash2, FileText, Check, Loader2, Sparkles, FolderPlus } from "lucide-react";
import { ConfirmationModal } from "@/components/ui/ConfirmationModal";
import { listCollections, createCollection, deleteCollection, CollectionItem } from "@/lib/api/workspace";
import { useToast } from "@/components/ui/Toast";

export function CollectionsView() {
  const toast = useToast();
  const [collections, setCollections] = useState<CollectionItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [newColName, setNewColName] = useState("");
  const [newColDesc, setNewColDesc] = useState("");
  const [newColColor, setNewColColor] = useState("#6366f1");
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; name: string } | null>(null);

  const fetchCollections = async () => {
    try {
      setIsLoading(true);
      const data = await listCollections();
      setCollections(data);
    } catch (err: any) {
      toast.error(err.message || "Failed to load collections.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCollections();
  }, []);

  const handleCreateCollection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newColName.trim()) return;
    try {
      const created = await createCollection({
        name: newColName.trim(),
        description: newColDesc.trim() || undefined,
        color: newColColor,
      });
      setCollections((prev) => [created, ...prev]);
      setNewColName("");
      setNewColDesc("");
      setIsCreating(false);
      toast.success(`Collection "${created.name}" created successfully.`);
    } catch (err: any) {
      toast.error(err.message || "Failed to create collection.");
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteCollection(deleteTarget.id);
      setCollections((prev) => prev.filter((c) => c.id !== deleteTarget.id));
      toast.success("Collection deleted.");
    } catch (err: any) {
      toast.error(err.message || "Failed to delete collection.");
    } finally {
      setDeleteTarget(null);
    }
  };

  const defaultPresets = [
    { name: "My Projects", color: "#6366f1" },
    { name: "College & Academics", color: "#ec4899" },
    { name: "Research Papers", color: "#06b6d4" },
    { name: "Interview Preparation", color: "#10b981" },
    { name: "Personal Knowledge", color: "#f59e0b" },
  ];

  return (
    <div className="flex-1 p-6 md:p-8 max-w-6xl mx-auto w-full space-y-6 overflow-y-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
            <FolderKanban className="w-6 h-6 text-indigo-400" />
            Knowledge Collections
          </h2>
          <p className="text-xs text-muted-foreground mt-1">
            Group related documents into dedicated intelligence domains for targeted context retrieval.
          </p>
        </div>
        <button
          onClick={() => setIsCreating(!isCreating)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-md transition-all cursor-pointer self-start sm:self-auto"
        >
          <FolderPlus className="w-4 h-4" />
          <span>New Collection</span>
        </button>
      </div>

      {/* Creation Modal / Form */}
      {isCreating && (
        <form onSubmit={handleCreateCollection} className="p-5 rounded-2xl bg-surface border border-border glass-panel space-y-4 animate-in fade-in duration-150">
          <h3 className="text-xs font-bold text-foreground uppercase tracking-wider">Create New Collection</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="Collection name (e.g., Quantum Research)"
              value={newColName}
              onChange={(e) => setNewColName(e.target.value)}
              className="px-3.5 py-2.5 rounded-xl bg-surface border border-border text-xs text-foreground focus:outline-none focus:border-indigo-500"
              required
            />
            <input
              type="text"
              placeholder="Description (optional)"
              value={newColDesc}
              onChange={(e) => setNewColDesc(e.target.value)}
              className="px-3.5 py-2.5 rounded-xl bg-surface border border-border text-xs text-foreground focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground font-semibold">Theme Color:</span>
            {["#6366f1", "#ec4899", "#06b6d4", "#10b981", "#f59e0b", "#8b5cf6"].map((color) => (
              <button
                key={color}
                type="button"
                onClick={() => setNewColColor(color)}
                className="w-6 h-6 rounded-full border-2 transition-transform cursor-pointer"
                style={{ backgroundColor: color, borderColor: newColColor === color ? "#ffffff" : "transparent" }}
              />
            ))}
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsCreating(false)}
              className="px-4 py-2 rounded-xl border border-border hover:bg-surface-hover text-xs font-semibold text-foreground cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md cursor-pointer"
            >
              Save Collection
            </button>
          </div>
        </form>
      )}

      {/* Grid of Collections */}
      {isLoading ? (
        <div className="py-16 text-center text-muted-foreground flex flex-col items-center gap-2">
          <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
          <span className="text-xs">Loading collection workspace...</span>
        </div>
      ) : collections.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {collections.map((col) => (
            <div
              key={col.id}
              className="p-5 rounded-2xl bg-surface border border-border hover:border-indigo-500/30 transition-all glass-panel flex flex-col justify-between group"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div
                      className="w-3.5 h-3.5 rounded-full shadow-sm"
                      style={{ backgroundColor: col.color || "#6366f1" }}
                    />
                    <h3 className="text-sm font-bold text-foreground group-hover:text-indigo-400 transition-colors">
                      {col.name}
                    </h3>
                  </div>
                  <button
                    onClick={() => setDeleteTarget({ id: col.id, name: col.name })}
                    className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-500/10 text-muted-foreground hover:text-red-400 transition-all cursor-pointer"
                    title="Delete collection"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                {col.description && (
                  <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">{col.description}</p>
                )}
              </div>

              <div className="pt-4 border-t border-border/50 mt-4 flex items-center justify-between text-[11px] text-muted-foreground">
                <span className="flex items-center gap-1.5 font-mono">
                  <FileText className="w-3.5 h-3.5 text-indigo-400" />
                  {col.document_count} {col.document_count === 1 ? "document" : "documents"}
                </span>
                <span>{col.created_at ? new Date(col.created_at).toLocaleDateString() : ""}</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-12 px-6 rounded-2xl bg-surface/50 border border-border text-center space-y-3">
          <FolderKanban className="w-8 h-8 text-indigo-400 mx-auto" />
          <h3 className="text-sm font-bold text-foreground">No collections created yet</h3>
          <p className="text-xs text-muted-foreground max-w-md mx-auto">
            Create your first knowledge collection to organize documents by project or subject area.
          </p>
          <div className="pt-2 flex flex-wrap justify-center gap-2">
            {defaultPresets.map((preset) => (
              <button
                key={preset.name}
                onClick={() => {
                  setNewColName(preset.name);
                  setNewColColor(preset.color);
                  setIsCreating(true);
                }}
                className="px-3 py-1.5 rounded-xl border border-border bg-surface hover:bg-surface-hover text-xs font-semibold text-foreground transition-all cursor-pointer"
              >
                + Add {preset.name}
              </button>
            ))}
          </div>
        </div>
      )}

      <ConfirmationModal
        isOpen={Boolean(deleteTarget)}
        title="Delete Knowledge Collection"
        message={`Are you sure you want to delete collection "${deleteTarget?.name || ""}"? Associated document bindings will be unlinked.`}
        confirmLabel="Delete"
        cancelLabel="Cancel"
        onConfirm={handleConfirmDelete}
        onClose={() => setDeleteTarget(null)}
      />
    </div>
  );
}
