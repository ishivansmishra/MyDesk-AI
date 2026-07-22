"use client";

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

export function useDashboardData() {
  const [events, setEvents] = useState<any[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      setLoading(true);
      const [eventsData, tasksData] = await Promise.all([api.getCalendarEvents(), api.getTasks()]);
      setEvents(eventsData);
      setTasks(tasksData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load workspace data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  return { events, tasks, loading, error, refresh };
}
