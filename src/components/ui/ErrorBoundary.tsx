"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error caught by ErrorBoundary:", error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#030712] flex items-center justify-center p-4 relative overflow-hidden select-none">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] rounded-full bg-rose-500/10 blur-[100px] pointer-events-none" />
          <div className="w-full max-w-md bg-[#0b0f19]/80 border border-rose-500/20 rounded-3xl p-6 md:p-8 shadow-2xl relative glass-panel text-center">
            <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center mx-auto mb-5 text-rose-400">
              <AlertTriangle className="w-6 h-6 animate-pulse" />
            </div>
            
            <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-2">
              System Error Encountered
            </h2>
            
            <p className="text-xs text-zinc-400 leading-relaxed mb-6">
              An unexpected client-side exception has occurred. The error has been logged, and you can attempt to restore your session.
            </p>

            {this.state.error && (
              <div className="bg-black/40 border border-white/5 rounded-2xl p-4 mb-6 text-left max-h-32 overflow-y-auto">
                <code className="text-[10px] font-mono text-zinc-500 leading-normal block break-all">
                  {this.state.error.toString()}
                </code>
              </div>
            )}

            <button
              onClick={this.handleReset}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-rose-600/20 active:scale-[0.98] transition-all cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Reset & Reload Session
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
