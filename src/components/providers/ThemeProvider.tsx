"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { Settings } from "@/types";

interface AppContextType {
  theme: "light" | "dark" | "system";
  setTheme: (theme: "light" | "dark" | "system") => void;
  settings: Omit<Settings, "theme">;
  updateSetting: <K extends keyof Omit<Settings, "theme">>(
    key: K,
    value: Omit<Settings, "theme">[K]
  ) => void;
  mounted: boolean;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<"light" | "dark" | "system">("dark");
  const [settings, setSettings] = useState<Omit<Settings, "theme">>({
    animationsEnabled: true,
    compactMode: false,
    soundEffectsEnabled: false,
    sendWithEnter: true,
    semanticChunkLimit: 5,
    similarityFiltering: true,
    chatRetention: true,
    responseStyle: "balanced",
    responseTone: "professional",
  });
  const [mounted, setMounted] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const storedTheme = localStorage.getItem("nova-theme") as
        | "light"
        | "dark"
        | "system"
        | null;
      const storedAnimations = localStorage.getItem("nova-animations");
      const storedCompact = localStorage.getItem("nova-compact");
      const storedSound = localStorage.getItem("nova-sound");
      const storedSendWithEnter = localStorage.getItem("nova-sendWithEnter");
      const storedChunkLimit = localStorage.getItem("nova-semanticChunkLimit");
      const storedSimilarity = localStorage.getItem("nova-similarityFiltering");
      const storedRetention = localStorage.getItem("nova-chatRetention");
      const storedStyle = localStorage.getItem("nova-responseStyle") as "concise" | "balanced" | "detailed" | null;
      const storedTone = localStorage.getItem("nova-responseTone") as "professional" | "friendly" | "technical" | null;

      setTimeout(() => {
        if (storedTheme) {
          setThemeState(storedTheme);
        }
        setSettings({
          animationsEnabled: storedAnimations !== "false",
          compactMode: storedCompact === "true",
          soundEffectsEnabled: storedSound === "true",
          sendWithEnter: storedSendWithEnter !== "false",
          semanticChunkLimit: storedChunkLimit ? parseInt(storedChunkLimit, 10) : 5,
          similarityFiltering: storedSimilarity !== "false",
          chatRetention: storedRetention !== "false",
          responseStyle: storedStyle || "balanced",
          responseTone: storedTone || "professional",
        });
        setMounted(true);
      }, 0);
    } catch (e) {
      console.error("Failed to read settings from localStorage", e);
      setTimeout(() => setMounted(true), 0);
    }
  }, []);

  // Synchronize theme with DOM
  useEffect(() => {
    if (!mounted) return;

    const root = document.documentElement;
    const applyTheme = (t: "light" | "dark" | "system") => {
      let isDark = false;
      if (t === "dark") {
        isDark = true;
      } else if (t === "system") {
        isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      }

      if (isDark) {
        root.classList.add("dark");
      } else {
        root.classList.remove("dark");
      }
    };

    applyTheme(theme);

    // If theme is system, listen to media query changes
    if (theme === "system") {
      const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
      const handleChange = () => applyTheme("system");
      mediaQuery.addEventListener("change", handleChange);
      return () => mediaQuery.removeEventListener("change", handleChange);
    }
  }, [theme, mounted]);

  // Synchronize settings with DOM / LocalStorage
  useEffect(() => {
    if (!mounted) return;
    const root = document.documentElement;
    
    if (settings.compactMode) {
      root.classList.add("compact-mode");
    } else {
      root.classList.remove("compact-mode");
    }
  }, [settings.compactMode, mounted]);

  const setTheme = (newTheme: "light" | "dark" | "system") => {
    setThemeState(newTheme);
    try {
      localStorage.setItem("nova-theme", newTheme);
    } catch (e) {
      console.error(e);
    }
  };

  const updateSetting = <K extends keyof Omit<Settings, "theme">>(
    key: K,
    value: Omit<Settings, "theme">[K]
  ) => {
    setSettings((prev) => {
      const updated = { ...prev, [key]: value };
      try {
        localStorage.setItem(`nova-${String(key).replace("Enabled", "")}`, String(value));
      } catch (e) {
        console.error(e);
      }
      return updated;
    });
  };

  return (
    <AppContext.Provider
      value={{
        theme,
        setTheme,
        settings,
        updateSetting,
        mounted,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
}
