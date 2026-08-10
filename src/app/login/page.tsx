"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Mail,
  Lock,
  ArrowRight,
  Sparkles,
  AlertCircle,
  Eye,
  EyeOff,
  Globe,
} from "lucide-react";
import { loginUser, registerUser, getMe } from "@/lib/api/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [infoNotice, setInfoNotice] = useState<string | null>(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true);

  // Check if session is already active
  useEffect(() => {
    getMe()
      .then(() => {
        router.push("/");
      })
      .catch(() => {
        setIsCheckingSession(false);
      });
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;

    setIsLoading(true);
    setAuthError(null);

    try {
      await loginUser(email, password);
      router.push("/");
    } catch (err: any) {
      setAuthError(err.message || "Invalid credentials. Please try again.");
      setIsLoading(false);
    }
  };

  if (isCheckingSession) {
    return (
      <div className="min-h-screen bg-[#070A12] flex items-center justify-center relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[350px] h-[350px] rounded-full bg-indigo-500/10 blur-[100px] pointer-events-none" />
        <div className="flex flex-col items-center gap-4 relative z-10">
          <div className="w-10 h-10 rounded-full border-2 border-t-indigo-500 border-r-transparent border-b-transparent border-l-transparent animate-spin" />
          <p className="text-zinc-400 text-sm font-medium tracking-wide">
            Syncing session...
          </p>
        </div>
      </div>
    );
  }

  const handleDemoLogin = async () => {
    setIsLoading(true);
    setAuthError(null);
    setEmail("demo@nova.ai");
    setPassword("demo12345");

    try {
      await loginUser("demo@nova.ai", "demo12345");
      router.push("/");
    } catch (err: any) {
      // Fallback: create demo user if login fails initially
      try {
        await registerUser("Demo Architect", "demo@nova.ai", "demo12345");
        router.push("/");
      } catch (regErr: any) {
        setAuthError(regErr.message || "Failed demo sign-in.");
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="min-h-screen bg-[#070A12] text-zinc-100 grid grid-cols-1 md:grid-cols-[1.1fr_0.9fr] relative overflow-hidden selection:bg-indigo-500/30">
      
      {/* LEFT MARKETING PANEL (Hidden on Mobile) */}
      <div className="hidden md:flex flex-col justify-between p-12 bg-zinc-950/60 relative overflow-hidden border-r border-white/5">
        {/* Glow Effects */}
        <div className="absolute top-1/2 left-1/3 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-indigo-500/5 blur-[120px] pointer-events-none animate-pulse-slow" />
        <div className="absolute bottom-1/4 right-1/4 w-[350px] h-[350px] rounded-full bg-cyan-500/5 blur-[120px] pointer-events-none" />

        {/* Header Logo */}
        <div className="flex items-center gap-3 relative z-10">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-0.5 shadow-lg shadow-indigo-500/20">
            <div className="w-full h-full bg-[#0b0f19] rounded-[10px] flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-indigo-400" />
            </div>
          </div>
          <span className="text-sm font-black tracking-wider text-white">NOVA AI</span>
        </div>

        {/* Feature Pitch */}
        <div className="space-y-6 my-auto max-w-md relative z-10">
          <h2 className="text-4xl font-extrabold tracking-tight text-white leading-tight">
            Intelligence that works with your knowledge.
          </h2>
          <p className="text-zinc-400 text-sm leading-relaxed">
            Experience a private, custom intelligence engine for document reasoning, deep web research, and autonomous sandbox coding.
          </p>
          <div className="space-y-4 pt-4">
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400 text-xs">
                ✓
              </div>
              <span className="text-sm text-zinc-300 font-medium">Conversational Multi-Modal AI</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400 text-xs">
                ✓
              </div>
              <span className="text-sm text-zinc-300 font-medium">Private Document Intelligence (RAG)</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400 text-xs">
                ✓
              </div>
              <span className="text-sm text-zinc-300 font-medium">Fast, Grounded Code Sandbox Answers</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-xs text-zinc-600 font-medium relative z-10">
          © 2026 NOVA AI. Platform OS Enterprise.
        </div>
      </div>

      {/* RIGHT AUTHENTICATION PANEL */}
      <div className="flex flex-col justify-center items-center p-6 md:p-12 relative">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[350px] h-[350px] rounded-full bg-indigo-500/5 blur-[90px] pointer-events-none" />

        <div className="w-full max-w-[420px] relative z-10 space-y-8">
          
          {/* Header (Logo + Title) */}
          <div className="space-y-2 text-left">
            <div className="md:hidden flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-0.5">
                <div className="w-full h-full bg-[#0b0f19] rounded-[6px] flex items-center justify-center">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                </div>
              </div>
              <span className="text-sm font-black tracking-wider text-white">NOVA AI</span>
            </div>

            <h1 className="text-3xl font-extrabold tracking-tight text-white">
              Welcome back
            </h1>
            <p className="text-sm text-zinc-400">
              Sign in to continue to your workspace.
            </p>
          </div>

          {authError && (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start gap-3 text-red-300 text-xs animate-in fade-in duration-200">
              <AlertCircle className="w-4.5 h-4.5 text-red-400 shrink-0 mt-0.5" />
              <span className="leading-relaxed">{authError}</span>
            </div>
          )}

          {infoNotice && (
            <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-start gap-3 text-indigo-300 text-xs animate-in fade-in duration-200">
              <Sparkles className="w-4.5 h-4.5 text-indigo-400 shrink-0 mt-0.5" />
              <span className="leading-relaxed">{infoNotice}</span>
            </div>
          )}

          {/* Quick Demo Sign In Banner */}
          <button
            type="button"
            onClick={handleDemoLogin}
            disabled={isLoading}
            className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600/20 via-indigo-500/10 to-cyan-500/20 border border-indigo-500/30 hover:border-indigo-500/60 text-indigo-300 hover:text-white font-semibold text-xs flex items-center justify-between transition-all group cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-400 group-hover:scale-110 transition-transform" />
              <span>1-Click Demo Sign In</span>
            </div>
            <span className="text-[10px] font-mono text-zinc-400 group-hover:text-indigo-200">demo@nova.ai →</span>
          </button>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            
            {/* Email */}
            <div className="space-y-2">
              <label className="text-xs font-semibold tracking-wide text-zinc-300 block">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Mail className="w-5 h-5 text-zinc-500" />
                </div>
                <input
                  type="email"
                  required
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full h-12 bg-zinc-950/40 border border-white/10 rounded-xl pl-12 pr-4 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition-all hover:border-white/20"
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold tracking-wide text-zinc-300 block">
                  Password
                </label>
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    setInfoNotice("Password reset is managed through your organization SSO admin.");
                  }}
                  className="text-xs text-indigo-400 hover:underline font-semibold transition-colors"
                >
                  Forgot password?
                </a>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock className="w-5 h-5 text-zinc-500" />
                </div>
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full h-12 bg-zinc-950/40 border border-white/10 rounded-xl pl-12 pr-12 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition-all hover:border-white/20"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-4 flex items-center text-zinc-500 hover:text-zinc-300 transition-colors cursor-pointer"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* Remember Me */}
            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2.5 cursor-pointer text-xs text-zinc-400 select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded border-white/10 bg-zinc-950 text-indigo-600 focus:ring-indigo-500/30"
                />
                <span>Remember session</span>
              </label>
            </div>

            {/* Primary CTA */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full h-12 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-xl shadow-indigo-600/10 hover:shadow-indigo-600/20 transition-all duration-200 flex items-center justify-center gap-2 group active:scale-[0.99] disabled:opacity-50 disabled:pointer-events-none mt-2 cursor-pointer"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-t-white border-r-transparent border-b-transparent border-l-transparent animate-spin rounded-full" />
              ) : (
                <>
                  <span>Continue to Workspace</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          {/* Social SSO Divider */}
          <div className="relative flex items-center justify-center py-2">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/5" />
            </div>
            <div className="relative px-4 bg-[#070A12] text-[10px] uppercase font-bold tracking-wider text-zinc-500">
              Or continue with
            </div>
          </div>

          {/* Social Buttons */}
          <div className="grid grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => setInfoNotice("Google SSO option is active for Enterprise domains.")}
              className="h-12 rounded-xl bg-zinc-950/40 border border-white/10 hover:bg-zinc-950 hover:border-white/20 text-xs font-semibold text-zinc-300 flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
                <path fill="#EA4335" d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.7 14.8 1 12 1 7.4 1 3.5 3.6 1.6 7.4l3.7 2.9C6.2 7.1 8.9 5 12 5z"/>
                <path fill="#4285F4" d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.8z"/>
                <path fill="#FBBC05" d="M5.3 14.7c-.2-.7-.4-1.4-.4-2.2s.2-1.5.4-2.2L1.6 7.4C.6 9.4 0 11.6 0 14s.6 4.6 1.6 6.6l3.7-2.9z"/>
                <path fill="#34A853" d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3.1 0-5.8-2.1-6.7-5.3L1.6 16c1.9 3.8 5.8 6.4 10.4 6.4z"/>
              </svg>
              <span>Google</span>
            </button>

            <button
              type="button"
              onClick={() => setInfoNotice("GitHub OAuth option is active for Enterprise domains.")}
              className="h-12 rounded-xl bg-zinc-950/40 border border-white/10 hover:bg-zinc-950 hover:border-white/20 text-xs font-semibold text-zinc-300 flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <Globe className="w-4 h-4 text-zinc-400 shrink-0" />
              <span>GitHub</span>
            </button>
          </div>

          {/* Footer Link */}
          <p className="text-center text-xs text-zinc-400">
            Don&apos;t have an account?{" "}
            <Link
              href="/register"
              className="text-indigo-400 font-semibold hover:underline transition-colors"
            >
              Create an account
            </Link>
          </p>

        </div>
      </div>
      
    </div>
  );
}
