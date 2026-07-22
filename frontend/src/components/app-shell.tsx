"use client";

import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  Bot,
  CalendarRange,
  ChevronRight,
  LayoutGrid,
  MessageSquareText,
  PanelLeftClose,
  PanelLeftOpen,
  Settings,
  Sparkles,
  CheckCircle2,
  PlugZap,
  UserCircle2,
  LogOut,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { api } from '@/lib/api';

const navItems = [
  { label: 'Overview', href: '/', icon: LayoutGrid },
  { label: 'New Chat', href: '/chat', icon: MessageSquareText },
  { label: 'Calendar', href: '/calendar', icon: CalendarRange },
  { label: 'Tasks', href: '/tasks', icon: CheckCircle2 },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    const token = window.localStorage.getItem('mydesk-auth-token');
    setAuthenticated(Boolean(token));
  }, [pathname]);

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch {
      // ignore and clear client state
    }
    window.localStorage.removeItem('mydesk-auth-token');
    setAuthenticated(false);
    router.push('/');
  };

  return (
    <div className="min-h-screen bg-transparent text-slate-100">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-4 py-4 lg:flex-row lg:px-6 lg:py-6">
        <motion.aside
          initial={false}
          animate={{ width: collapsed ? 88 : 260 }}
          transition={{ type: 'spring', stiffness: 220, damping: 24 }}
          className="relative mb-4 overflow-hidden rounded-[28px] border border-white/10 bg-slate-900/70 p-3 shadow-2xl shadow-blue-950/30 backdrop-blur-xl lg:mb-0 lg:mr-4"
        >
          <div className="flex items-center justify-between px-2 py-2">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 via-indigo-500 to-violet-500 shadow-lg shadow-blue-500/20">
                <Bot className="h-5 w-5" />
              </div>
              {!collapsed && <div>
                <p className="text-sm font-semibold">MyDesk AI</p>
                <p className="text-xs text-slate-400">Workspace OS</p>
              </div>}
            </div>
            <button
              onClick={() => setCollapsed((value) => !value)}
              className="rounded-full border border-white/10 bg-white/5 p-2 text-slate-300 transition hover:bg-white/10"
              aria-label="Toggle sidebar"
            >
              {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
            </button>
          </div>

          <div className="mt-6 rounded-2xl border border-blue-500/20 bg-gradient-to-br from-blue-500/10 to-violet-500/10 p-3">
            {!collapsed ? (
              <div>
                <div className="flex items-center gap-2 text-sm font-medium text-blue-200">
                  <Sparkles className="h-4 w-4" />
                  Workspace
                </div>
                <p className="mt-2 text-sm text-slate-300">Connected to Google Workspace and AI tools.</p>
              </div>
            ) : (
              <div className="flex justify-center">
                <Sparkles className="h-5 w-5 text-blue-200" />
              </div>
            )}
          </div>

          <nav className="mt-6 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.label}
                  href={item.href}
                  className="group flex items-center gap-3 rounded-2xl px-3 py-3 text-sm text-slate-300 transition hover:bg-white/10 hover:text-white"
                >
                  <Icon className="h-4 w-4" />
                  {!collapsed && <span>{item.label}</span>}
                  {!collapsed && <ChevronRight className="ml-auto h-4 w-4 opacity-0 transition group-hover:opacity-100" />}
                </Link>
              );
            })}
          </nav>

          <div className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-3">
            {authenticated ? (
              <button onClick={() => void handleLogout()} className="flex w-full items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300 transition hover:bg-white/10">
                <LogOut className="h-4 w-4" />
                {!collapsed && <span>Logout</span>}
              </button>
            ) : (
              <Link href="/login" className="flex items-center gap-2 rounded-2xl border border-blue-400/20 bg-blue-500/10 px-3 py-2 text-sm text-blue-200 transition hover:bg-blue-500/20">
                <Sparkles className="h-4 w-4" />
                {!collapsed && <span>Sign in</span>}
              </Link>
            )}
          </div>

          <div className="mt-8 rounded-2xl border border-white/10 bg-white/5 p-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-violet-500 text-white">
                <UserCircle2 className="h-5 w-5" />
              </div>
              {!collapsed && (
                <div>
                  <p className="text-sm font-medium">Google Workspace</p>
                  <p className="text-xs text-slate-400">Sign in to see your profile</p>
                </div>
              )}
            </div>
          </div>
        </motion.aside>

        <main className="flex-1 rounded-[32px] border border-white/10 bg-slate-900/60 p-4 shadow-2xl shadow-slate-950/30 backdrop-blur-xl sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
