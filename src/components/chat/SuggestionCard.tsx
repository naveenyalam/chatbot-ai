"use client";

import React from "react";
import { ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { useApp } from "@/components/providers/ThemeProvider";

interface SuggestionCardProps {
  title: string;
  description: string;
  prompt: string;
  icon: React.ComponentType<{ className?: string }>;
  onClick: (prompt: string) => void;
  className?: string;
}

export function SuggestionCard({
  title,
  description,
  prompt,
  icon: Icon,
  onClick,
  className,
}: SuggestionCardProps) {
  const { settings } = useApp();
  const animate = settings.animationsEnabled;

  return (
    <button
      onClick={() => onClick(prompt)}
      className={cn(
        "text-left flex flex-col justify-between p-4.5 rounded-2xl border border-border-subtle bg-surface-primary/45 hover:bg-surface-secondary/60 hover:border-accent/40 dark:hover:border-accent/40 select-none group w-full transition-all duration-300",
        animate && "hover:-translate-y-1 hover:scale-[1.01] hover:shadow-[0_8px_30px_rgba(99,102,241,0.06)] dark:hover:shadow-[0_8px_30px_rgba(129,140,248,0.06)]",
        className
      )}
    >
      <div className="flex items-start justify-between w-full">
        {/* Card Icon */}
        <div className="p-2 rounded-xl bg-surface-secondary/80 border border-border-subtle group-hover:border-accent/25 transition-all text-text-muted group-hover:text-accent">
          <Icon className="w-4.5 h-4.5" />
        </div>

        {/* Hover Arrow Link */}
        <ArrowUpRight
          className={cn(
            "w-4 h-4 text-text-muted group-hover:text-accent transition-all duration-300",
            animate && "transform translate-y-1 -translate-x-1 opacity-0 group-hover:translate-y-0 group-hover:translate-x-0 group-hover:opacity-100"
          )}
        />
      </div>

      <div className="mt-4">
        <h3 className="text-sm font-semibold text-text-primary group-hover:text-accent transition-colors">
          {title}
        </h3>
        <p className="text-xs text-text-muted mt-1 leading-relaxed">
          {description}
        </p>
      </div>
    </button>
  );
}
