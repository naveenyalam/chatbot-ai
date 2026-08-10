"use client";

import React, { useState, useEffect } from "react";
import { BookOpen, Plus, Search, Star, Trash2, Edit2, ArrowRight, Loader2, Sparkles } from "lucide-react";
import { ConfirmationModal } from "@/components/ui/ConfirmationModal";
import { listPrompts, createPrompt, updatePrompt, deletePrompt, PromptItem } from "@/lib/api/workspace";
import { useToast } from "@/components/ui/Toast";

interface PromptLibraryProps {
  onInsertPrompt?: (content: string) => void;
}

export function PromptLibrary({ onInsertPrompt }: PromptLibraryProps) {
  const toast = useToast();
  const [prompts, setPrompts] = useState<PromptItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");
  const [isCreating, setIsCreating] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("Productivity");
  const [varInput, setVarInput] = useState("");

  const categories = ["All", "Coding", "Study", "Writing", "Research", "Business", "Productivity"];

  const fetchPrompts = async () => {
    try {
      setIsLoading(true);
      const data = await listPrompts();
      setPrompts(data);
    } catch (err: any) {
      toast.error(err.message || "Failed to load prompt library.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPrompts();
  }, []);

  const handleCreatePrompt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;

    // Detect variables like {{topic}}, {{level}}
    const detectedVars = Array.from(content.matchAll(/\{\{([^}]+)\}\}/g)).map((m) => m[1].trim());

    try {
      const created = await createPrompt({
        title: title.trim(),
        content: content.trim(),
        category,
        variables: Array.from(new Set(detectedVars)),
      });
      setPrompts((prev) => [created, ...prev]);
      setTitle("");
      setContent("");
      setIsCreating(false);
      toast.success("Prompt saved to library.");
    } catch (err: any) {
      toast.error(err.message || "Failed to create prompt.");
    }
  };

  const handleToggleFavorite = async (p: PromptItem) => {
    try {
      const updated = await updatePrompt(p.id, { is_favorite: !p.is_favorite });
      setPrompts((prev) => prev.map((item) => (item.id === p.id ? updated : item)));
    } catch (err: any) {
      toast.error(err.message || "Failed to update prompt.");
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTargetId) return;
    try {
      await deletePrompt(deleteTargetId);
      setPrompts((prev) => prev.filter((p) => p.id !== deleteTargetId));
      toast.success("Prompt removed.");
    } catch (err: any) {
      toast.error(err.message || "Failed to delete prompt.");
    } finally {
      setDeleteTargetId(null);
    }
  };

  const filteredPrompts = prompts.filter((p) => {
    const matchesCategory = activeCategory === "All" || p.category.toLowerCase() === activeCategory.toLowerCase();
    const matchesSearch = p.title.toLowerCase().includes(searchQuery.toLowerCase()) || p.content.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="flex-1 p-6 md:p-8 max-w-6xl mx-auto w-full space-y-6 overflow-y-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-foreground">Prompt Library</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Create, favorite, and organize reusable system prompts with variable support.
            </p>
          </div>
        </div>

        <button
          onClick={() => setIsCreating(!isCreating)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-md transition-all cursor-pointer self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>New Prompt</span>
        </button>
      </div>

      {/* Creation Modal / Form */}
      {isCreating && (
        <form onSubmit={handleCreatePrompt} className="p-5 rounded-2xl bg-surface border border-border glass-panel space-y-4 animate-in fade-in duration-150">
          <h3 className="text-xs font-bold text-foreground uppercase tracking-wider">Create Custom Prompt</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="Prompt Title (e.g., Code Refactoring Assistant)"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="px-3.5 py-2.5 rounded-xl bg-surface border border-border text-xs text-foreground focus:outline-none focus:border-purple-500"
              required
            />
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="px-3.5 py-2.5 rounded-xl bg-surface border border-border text-xs text-foreground focus:outline-none focus:border-purple-500"
            >
              {categories.filter((c) => c !== "All").map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
          <textarea
            placeholder="Prompt content. Use {{variable_name}} for dynamic fields (e.g. Explain {{topic}} at {{level}} level)."
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="w-full h-32 p-3.5 rounded-xl bg-surface border border-border text-xs font-mono text-foreground focus:outline-none focus:border-purple-500 resize-none"
            required
          />
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setIsCreating(false)}
              className="px-4 py-2 rounded-xl border border-border hover:bg-surface-hover text-xs font-semibold text-foreground cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md cursor-pointer"
            >
              Save Prompt
            </button>
          </div>
        </form>
      )}

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0 scrollbar-none">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                activeCategory === cat
                  ? "bg-purple-600/10 text-purple-600 dark:text-purple-300 border border-purple-500/20"
                  : "bg-surface border border-border text-muted-foreground hover:text-foreground hover:bg-surface-hover"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search prompts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full py-2 pl-8 pr-3 rounded-xl bg-surface border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-purple-500"
          />
        </div>
      </div>

      {/* Prompts List Grid */}
      {isLoading ? (
        <div className="py-16 text-center text-muted-foreground flex flex-col items-center gap-2">
          <Loader2 className="w-6 h-6 animate-spin text-purple-400" />
          <span className="text-xs">Loading prompt library...</span>
        </div>
      ) : filteredPrompts.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredPrompts.map((p) => (
            <div key={p.id} className="p-5 rounded-2xl bg-surface border border-border hover:border-purple-500/30 transition-all glass-panel flex flex-col justify-between group space-y-3">
              <div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 text-[10px] font-bold uppercase tracking-wider">
                      {p.category}
                    </span>
                    <h3 className="text-sm font-bold text-foreground group-hover:text-purple-400 transition-colors">{p.title}</h3>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleToggleFavorite(p)}
                      className={`p-1.5 rounded-lg hover:bg-surface-hover transition-colors cursor-pointer ${p.is_favorite ? "text-amber-400" : "text-muted-foreground"}`}
                    >
                      <Star className="w-3.5 h-3.5 fill-current" />
                    </button>
                    <button
                      onClick={() => setDeleteTargetId(p.id)}
                      className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-500/10 text-muted-foreground hover:text-red-400 transition-all cursor-pointer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
                <p className="text-xs font-mono text-muted-foreground mt-2 line-clamp-3 bg-surface/50 p-2.5 rounded-xl border border-border/50">
                  {p.content}
                </p>
              </div>

              {p.variables && p.variables.length > 0 && (
                <div className="flex items-center gap-1 flex-wrap">
                  <span className="text-[10px] text-muted-foreground font-semibold">Variables:</span>
                  {p.variables.map((v) => (
                    <span key={v} className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 text-[10px] font-mono border border-indigo-500/20">
                      {`{{${v}}}`}
                    </span>
                  ))}
                </div>
              )}

              {onInsertPrompt && (
                <div className="pt-2 border-t border-border/50 flex justify-end">
                  <button
                    onClick={() => {
                      onInsertPrompt(p.content);
                      toast.success(`Prompt "${p.title}" inserted into chat.`);
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-purple-600/10 hover:bg-purple-600/20 text-purple-400 text-xs font-semibold transition-all cursor-pointer"
                  >
                    <span>Use Prompt</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="py-12 px-6 rounded-2xl bg-surface/50 border border-border text-center space-y-3">
          <BookOpen className="w-8 h-8 text-purple-400 mx-auto" />
          <h3 className="text-sm font-bold text-foreground">No prompts found in library</h3>
          <p className="text-xs text-muted-foreground">Add custom prompts or adjust your category search filter.</p>
        </div>
      )}

      <ConfirmationModal
        isOpen={Boolean(deleteTargetId)}
        title="Delete Prompt"
        message="Are you sure you want to delete this prompt template? It will be removed permanently from your prompt library."
        confirmLabel="Delete"
        cancelLabel="Cancel"
        onConfirm={handleConfirmDelete}
        onClose={() => setDeleteTargetId(null)}
      />
    </div>
  );
}
