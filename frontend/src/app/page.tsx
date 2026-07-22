"use client";

import { motion } from 'framer-motion';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowRight,
  Brain,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Sparkles,
  Zap,
  Loader2,
  AlertCircle,
  ShieldCheck,
} from 'lucide-react';
import { useDashboardData } from '@/hooks/use-dashboard-data';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';

const quickActions = [
  { title: 'Summarize inbox', hint: 'Turn emails into action items' },
  { title: 'Plan today', hint: 'Outline your most important work' },
  { title: 'Draft reply', hint: 'Create polished responses instantly' },
];

export default function HomePage() {
  const router = useRouter();
  const { events, tasks, loading, error, refresh } = useDashboardData();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const connected = params.get('connected') === '1';
    if (token) {
      console.debug('OAuth callback token received, storing auth token');
      window.localStorage.setItem('mydesk-auth-token', token);
      params.delete('token');
      params.delete('connected');
      const queryString = params.toString();
      const path = `${window.location.pathname}${queryString ? `?${queryString}` : ''}`;
      router.replace(path);
    } else if (connected) {
      console.debug('OAuth callback completed without token');
      router.replace(window.location.pathname);
    }
  }, [router]);

  return (
    <div className="space-y-6">
      <motion.header initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} className="rounded-[28px] border border-white/10 bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 p-6 shadow-glow">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-blue-400/20 bg-blue-500/10 px-3 py-1 text-sm text-blue-200">
              <Sparkles className="h-4 w-4" />
              Premium AI workspace assistant
            </div>
            <h1 className="mt-4 text-3xl font-semibold tracking-tight text-white sm:text-4xl">Your work, orchestrated beautifully.</h1>
            <p className="mt-3 max-w-xl text-sm leading-7 text-slate-300 sm:text-base">Turn Google Calendar, Tasks, Gmail, and Drive into one calm command center with elegant AI assistance.</p>
          </div>
          <Button className="bg-gradient-to-r from-blue-500 to-violet-500 text-white hover:opacity-90">
            <Brain className="mr-2 h-4 w-4" />
            Start new AI workflow
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </motion.header>

      <div className="grid gap-6 xl:grid-cols-[1.5fr_0.9fr]">
        <div className="space-y-6">
          <Card className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Quick actions</p>
                <h2 className="mt-1 text-xl font-semibold text-white">Ready for your next move</h2>
              </div>
              <div className="rounded-full border border-emerald-400/20 bg-emerald-500/10 px-3 py-1 text-sm text-emerald-300">4 suggestions</div>
            </div>
            <div className="mt-5 grid gap-3 md:grid-cols-3">
              {quickActions.map((action) => (
                <motion.button key={action.title} whileHover={{ y: -3, scale: 1.01 }} className="rounded-2xl border border-white/10 bg-white/5 p-4 text-left transition hover:border-blue-400/30 hover:bg-white/10">
                  <div className="flex items-center gap-2 text-sm font-medium text-white">
                    <Zap className="h-4 w-4 text-blue-400" />
                    {action.title}
                  </div>
                  <p className="mt-2 text-sm text-slate-400">{action.hint}</p>
                </motion.button>
              ))}
            </div>
          </Card>

          <Card className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Today</p>
                <h2 className="mt-1 text-xl font-semibold text-white">Your priorities</h2>
              </div>
              <Button onClick={refresh} className="bg-white/10">Refresh</Button>
            </div>
            {loading ? (
              <div className="mt-5 flex items-center gap-3 text-sm text-slate-400"><Loader2 className="h-4 w-4 animate-spin" />Loading workspace data...</div>
            ) : error ? (
              <div className="mt-5 flex items-center gap-3 rounded-2xl border border-danger/20 bg-danger/10 p-4 text-sm text-danger"><AlertCircle className="h-4 w-4" />{error}</div>
            ) : tasks.length === 0 ? (
              <div className="mt-5"><EmptyState title="No tasks available" description="Sign in and connect Google Tasks to see your real work items here." /></div>
            ) : (
              <div className="mt-5 space-y-3">
                {tasks.slice(0, 3).map((task) => (
                  <div key={task.id} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                    <div className="flex items-center gap-3">
                      <CheckCircle2 className={`h-4 w-4 ${task.completed ? 'text-emerald-400' : 'text-slate-400'}`} />
                      <span className="text-sm text-slate-200">{task.title}</span>
                    </div>
                    <span className="text-sm text-slate-400">{task.completed ? 'Complete' : 'In progress'}</span>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Upcoming</p>
                <h2 className="mt-1 text-xl font-semibold text-white">Meetings</h2>
              </div>
              <CalendarDays className="h-5 w-5 text-blue-400" />
            </div>
            {loading ? (
              <div className="mt-5 flex items-center gap-3 text-sm text-slate-400"><Loader2 className="h-4 w-4 animate-spin" />Pulling calendar events...</div>
            ) : error ? (
              <div className="mt-5 text-sm text-danger">{error}</div>
            ) : events.length === 0 ? (
              <div className="mt-5"><EmptyState title="Connect your calendar" description="Sign in with Google to view your real meetings and upcoming events." /></div>
            ) : (
              <div className="mt-5 space-y-3">
                {events.slice(0, 3).map((event) => (
                  <div key={event.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-white">{event.summary}</p>
                      <div className="rounded-full bg-blue-500/10 px-2.5 py-1 text-xs text-blue-200">{event.start}</div>
                    </div>
                    <p className="mt-2 text-sm text-slate-400">{event.end}</p>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card className="bg-gradient-to-br from-blue-500/15 to-violet-500/10 p-5">
            <div className="flex items-center gap-2 text-sm text-blue-200"><ShieldCheck className="h-4 w-4" />Secure access</div>
            <div className="mt-4">
              <p className="text-2xl font-semibold text-white">Protected by Google sign-in</p>
              <p className="mt-2 text-sm text-slate-300">Your workspace data stays private until you authenticate with Google.</p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
