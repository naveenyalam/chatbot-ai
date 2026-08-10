"use client";

import React from "react";
import { Sparkles } from "lucide-react";
import { useApp } from "@/components/providers/ThemeProvider";

export function ThinkingIndicator() {
  const { settings } = useApp();
  const animate = settings.animationsEnabled;
  const [elapsed, setElapsed] = React.useState(0);

  React.useEffect(() => {
    const startTime = Date.now();
    const interval = setInterval(() => {
      setElapsed((Date.now() - startTime) / 1000);
    }, 100);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-start gap-3 my-4 select-none w-full">
      {/* Visual Indicator Box */}
      <div className="relative flex items-center justify-center w-16 h-16 bg-surface-secondary/40 border border-border-subtle/50 rounded-2xl overflow-hidden glass-panel">
        
        {/* Glow backdrop */}
        <div className="absolute inset-0 bg-radial from-accent/15 via-transparent to-transparent blur-md animate-pulse" />

        {/* Orbit Ring */}
        <div 
          className={`absolute w-10 h-10 border border-dashed border-accent/25 rounded-full ${
            animate ? "animate-[spin_8s_linear_infinite]" : ""
          }`} 
        />

        {/* Orbit Dots */}
        <div 
          className={`absolute w-12 h-12 ${
            animate ? "animate-[spin_4s_linear_infinite]" : ""
          }`}
        >
          <span className="absolute top-0 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-accent rounded-full shadow-[0_0_8px_rgba(99,102,241,0.8)]" />
          <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-indigo-400 rounded-full opacity-60" />
        </div>

        {/* Center pulsing diamond / sparkles */}
        <div className={animate ? "animate-pulse" : ""}>
          <Sparkles className="w-4 h-4 text-accent" />
        </div>
      </div>

      {/* Thinking Status Text */}
      <div className="flex items-center gap-1.5 pl-1.5 text-text-muted">
        <span className="text-[10px] md:text-xs font-bold tracking-widest uppercase animate-pulse">
          Thinking ({elapsed.toFixed(1)}s)
        </span>
        <span className="flex gap-1">
          <span className="w-1 h-1 rounded-full bg-accent animate-[bounce_1.4s_infinite_0ms]" />
          <span className="w-1 h-1 rounded-full bg-accent animate-[bounce_1.4s_infinite_200ms]" />
          <span className="w-1 h-1 rounded-full bg-accent animate-[bounce_1.4s_infinite_400ms]" />
        </span>
      </div>
    </div>
  );
}
