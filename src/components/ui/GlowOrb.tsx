"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { useApp } from "@/components/providers/ThemeProvider";

export function GlowOrb({ className }: { className?: string }) {
  const { settings } = useApp();
  const animate = settings.animationsEnabled;

  return (
    <div
      className={cn(
        "relative w-64 h-64 flex items-center justify-center select-none",
        animate && "animate-glow",
        className
      )}
    >
      {/* Ambient background glow */}
      <div className="absolute inset-0 bg-gradient-to-tr from-accent/20 via-cyan-500/10 to-pink-500/10 blur-3xl opacity-60 rounded-full" />

      {/* Layer 3: Outer atmospheric glow (Slowest rotation) */}
      <div
        className={cn(
          "absolute w-56 h-56 rounded-full bg-gradient-to-tr from-violet-500/20 via-cyan-500/10 to-transparent blur-xl border border-white/5",
          animate && "animate-spin-slow"
        )}
      />

      {/* Layer 2: Mid glow layer (Opposite rotation, pulsing scale) */}
      <div
        className={cn(
          "absolute w-44 h-44 rounded-full bg-gradient-to-br from-indigo-500/20 via-pink-500/15 to-cyan-500/20 blur-md border border-white/10 dark:border-white/5",
          animate && "animate-spin-reverse animate-pulse-slow"
        )}
      />

      {/* Layer 1: Core (Central high-density liquid core) */}
      <div className="absolute w-32 h-32 rounded-full overflow-hidden flex items-center justify-center shadow-inner">
        {/* Liquid gradient fill */}
        <div
          className={cn(
            "absolute inset-0 bg-gradient-to-tr from-indigo-600/70 via-violet-500/50 to-cyan-400/70 opacity-90",
            animate && "animate-float-slow"
          )}
        />
        {/* Soft highlight */}
        <div className="absolute top-1 left-4 right-4 h-12 bg-white/20 blur-[2px] rounded-full transform -rotate-12" />
        {/* Core center */}
        <div className="absolute w-16 h-16 rounded-full bg-white/10 dark:bg-white/5 blur-sm" />
      </div>

      {/* Floating Particles (Rendered only if animations are enabled) */}
      {animate && (
        <div className="absolute inset-0 pointer-events-none overflow-visible">
          {[
            { delay: "0s", top: "10%", left: "20%", size: "4px" },
            { delay: "1.5s", top: "80%", left: "75%", size: "6px" },
            { delay: "3s", top: "30%", left: "85%", size: "5px" },
            { delay: "4.5s", top: "70%", left: "15%", size: "3px" },
            { delay: "2s", top: "50%", left: "5%", size: "4px" },
            { delay: "5.5s", top: "25%", left: "70%", size: "5px" },
          ].map((particle, idx) => (
            <span
              key={idx}
              className="absolute bg-cyan-400/40 rounded-full animate-float blur-[1px]"
              style={{
                top: particle.top,
                left: particle.left,
                width: particle.size,
                height: particle.size,
                animationDelay: particle.delay,
                animationDuration: `${6 + (idx % 3) * 2}s`,
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
