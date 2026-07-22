"use client";

import { useEffect, useState } from 'react';
import { CalendarDays, Loader2, Plus, RefreshCw, Lock } from 'lucide-react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';

export default function CalendarPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState('');
  const [authenticated, setAuthenticated] = useState(false);

  const formatDateTime = (value: string) => {
    if (!value) return '-';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
  };

  const getDefaultEventTimes = () => {
    const now = new Date();
    const nextHour = new Date(now);
    nextHour.setMinutes(0, 0, 0);
    nextHour.setHours(now.getHours() + 1);
    const end = new Date(nextHour);
    end.setHours(nextHour.getHours() + 1);
    return { start: nextHour.toISOString(), end: end.toISOString() };
  };

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const data = await api.getCalendarEvents();
      setEvents(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load events');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const token = window.localStorage.getItem('mydesk-auth-token');
    setAuthenticated(Boolean(token));
    if (token) {
      void fetchEvents();
    } else {
      setLoading(false);
    }
  }, []);

  const createEvent = async () => {
    if (!summary.trim()) return;
    try {
      const { start, end } = getDefaultEventTimes();
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      await api.createCalendarEvent({ summary, start, end, timezone });
      setSummary('');
      await fetchEvents();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create event');
    }
  };

  return (
    <div className="space-y-6">
      <Card className="p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm text-slate-400">Calendar</p>
            <h1 className="text-2xl font-semibold text-white">Google Calendar workspace</h1>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={fetchEvents} className="bg-white/10"><RefreshCw className="mr-2 h-4 w-4" />Refresh</Button>
          </div>
        </div>
        <div className="mt-4 flex flex-col gap-3 rounded-2xl border border-white/10 bg-slate-950/70 p-3 sm:flex-row">
          <input value={summary} onChange={(e) => setSummary(e.target.value)} placeholder={authenticated ? 'Add a meeting or event' : 'Sign in to create calendar events'} className="flex-1 rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none placeholder:text-slate-500" disabled={!authenticated} />
          <Button onClick={createEvent} className="bg-gradient-to-r from-blue-500 to-violet-500 text-white" disabled={!authenticated}><Plus className="mr-2 h-4 w-4" />Create event</Button>
        </div>
      </Card>

      <Card className="p-5">
        <div className="flex items-center gap-2 text-sm text-slate-400"><CalendarDays className="h-4 w-4" />Upcoming events</div>
        {loading ? (
          <div className="mt-6 flex items-center gap-3 text-sm text-slate-400"><Loader2 className="h-4 w-4 animate-spin" />Loading events from the backend...</div>
        ) : error ? (
          <div className="mt-6 text-sm text-danger">{error}</div>
        ) : !authenticated ? (
          <div className="mt-6 flex items-center gap-3 rounded-2xl border border-dashed border-white/10 bg-white/5 p-4 text-sm text-slate-400"><Lock className="h-4 w-4" />Sign in with Google to view your real calendar events.</div>
        ) : events.length === 0 ? (
          <div className="mt-6"><EmptyState title="No calendar events yet" description="Create one to see it appear here." /></div>
        ) : (
          <div className="mt-6 grid gap-3 md:grid-cols-2">
            {events.map((event) => (
              <div key={event.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-white">{event.summary}</p>
                    <p className="mt-1 text-xs text-slate-400">{formatDateTime(event.start)}</p>
                  </div>
                  <span className="rounded-full bg-blue-500/10 px-2.5 py-1 text-xs text-blue-200">{formatDateTime(event.end)}</span>
                </div>
                {event.timezone ? <p className="mt-2 text-xs uppercase tracking-[0.16em] text-slate-500">Timezone: {event.timezone}</p> : null}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
