"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { useApp } from "@/components/providers/ThemeProvider";

interface GlassPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  hoverGlow?: boolean;
  borderAccent?: boolean;
}

export function GlassPanel({
  children,
  className,
  hoverGlow = false,
  borderAccent = false,
  ...props
}: GlassPanelProps) {
  const { settings } = useApp();

  return (
    <div
      className={cn(
        "glass-panel rounded-2xl p-6 transition-all duration-300",
        borderAccent && "border-accent/10 dark:border-accent/20",
        hoverGlow &&
          settings.animationsEnabled &&
          "hover:border-accent/30 dark:hover:border-accent/40 hover:shadow-[0_0_20px_rgba(99,102,241,0.08)] dark:hover:shadow-[0_0_25px_rgba(129,140,248,0.08)] hover:-translate-y-[2px]",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
