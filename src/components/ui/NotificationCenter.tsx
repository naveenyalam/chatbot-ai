"use client";

import React, { useState, useEffect, useRef } from "react";
import { Bell, Check, CheckCheck, FileText, Bot, Search, Download, AlertCircle, Info, X } from "lucide-react";
import { listNotifications, markNotificationsRead, NotificationItem } from "@/lib/api/workspace";
import { cn } from "@/lib/utils";

export function NotificationCenter() {
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const fetchNotifications = async () => {
    try {
      setIsLoading(true);
      const data = await listNotifications();
      setUnreadCount(data.unread_count);
      setNotifications(data.notifications);
    } catch (err) {
      // Ignore initial load error if unauthorized or offline
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  const handleMarkAllRead = async () => {
    try {
      await markNotificationsRead(undefined, true);
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error("Failed to mark notifications read", err);
    }
  };

  const handleMarkSingleRead = async (id: string) => {
    try {
      await markNotificationsRead([id], false);
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error("Failed to mark notification read", err);
    }
  };

  const getCategoryIcon = (category: string, type: string) => {
    if (type === "error") return AlertCircle;
    switch (category) {
      case "document": return FileText;
      case "agent": return Bot;
      case "research": return Search;
      case "export": return Download;
      default: return Info;
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-xl hover:bg-surface-hover text-muted-foreground hover:text-foreground transition-all cursor-pointer"
        aria-label="Notification Center"
      >
        <Bell className="w-4 h-4" />
        {unreadCount > 0 && (
          <span className="absolute top-1.5 right-1.5 min-w-[16px] h-4 px-1 rounded-full bg-accent text-white text-[10px] font-bold flex items-center justify-center animate-pulse">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-80 sm:w-96 bg-surface-elevated border border-border rounded-2xl shadow-2xl glass-panel p-3 z-55 animate-in fade-in slide-in-from-top-1 duration-150">
          <div className="flex items-center justify-between border-b border-border pb-2.5 mb-2">
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-bold text-foreground">Notifications</h3>
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 rounded-full bg-accent/10 text-accent text-[10px] font-semibold">
                  {unreadCount} unread
                </span>
              )}
            </div>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-[11px] text-accent hover:underline flex items-center gap-1 cursor-pointer font-medium"
              >
                <CheckCheck className="w-3.5 h-3.5" />
                Mark all read
              </button>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto space-y-1.5 pr-1">
            {notifications.length > 0 ? (
              notifications.map((n) => {
                const Icon = getCategoryIcon(n.category, n.type);
                return (
                  <div
                    key={n.id}
                    onClick={() => !n.is_read && handleMarkSingleRead(n.id)}
                    className={cn(
                      "p-2.5 rounded-xl border text-left transition-all cursor-pointer flex items-start gap-2.5",
                      n.is_read
                        ? "bg-surface/40 border-border/50 opacity-75"
                        : "bg-surface border-border shadow-sm hover:border-accent/30"
                    )}
                  >
                    <div
                      className={cn(
                        "p-1.5 rounded-lg border mt-0.5 flex-shrink-0",
                        n.type === "error"
                          ? "bg-red-500/10 border-red-500/20 text-red-400"
                          : n.type === "success"
                          ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                          : "bg-indigo-500/10 border-indigo-500/20 text-indigo-400"
                      )}
                    >
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <div className="flex-grow min-w-0">
                      <div className="flex items-center justify-between gap-1">
                        <p className="text-xs font-semibold text-foreground truncate">{n.title}</p>
                        {!n.is_read && <span className="w-1.5 h-1.5 rounded-full bg-accent flex-shrink-0" />}
                      </div>
                      <p className="text-[11px] text-muted-foreground leading-normal mt-0.5 line-clamp-2">{n.message}</p>
                      <p className="text-[9px] text-muted-foreground/60 mt-1 font-mono">
                        {n.created_at ? new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "Just now"}
                      </p>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="py-8 text-center text-muted-foreground text-xs italic">
                No notifications right now
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
