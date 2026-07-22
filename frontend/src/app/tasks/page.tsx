"use client";

import { useEffect, useState } from 'react';
import { CheckCircle2, Loader2, Plus, RefreshCw, Lock } from 'lucide-react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';

export default function TasksPage() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [title, setTitle] = useState('');
  const [authenticated, setAuthenticated] = useState(false);

  const formatDueDate = (value: string | null | undefined) => {
    if (!value) return 'No due date';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
  };

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const data = await api.getTasks();
      setTasks(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load tasks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const token = window.localStorage.getItem('mydesk-auth-token');
    setAuthenticated(Boolean(token));
    if (token) {
      void fetchTasks();
    } else {
      setLoading(false);
    }
  }, []);

  const createTask = async () => {
    if (!title.trim()) return;
    try {
      await api.createTask({ title });
      setTitle('');
      await fetchTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create task');
    }
  };

  const toggleTask = async (task: any) => {
    try {
      await api.updateTask(task.id, { completed: !task.completed });
      await fetchTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update task');
    }
  };

  return (
    <div className="space-y-6">
      <Card className="p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm text-slate-400">Tasks</p>
            <h1 className="text-2xl font-semibold text-white">Google Tasks board</h1>
          </div>
          <Button onClick={fetchTasks} className="bg-white/10"><RefreshCw className="mr-2 h-4 w-4" />Refresh</Button>
        </div>
        <div className="mt-4 flex flex-col gap-3 rounded-2xl border border-white/10 bg-slate-950/70 p-3 sm:flex-row">
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder={authenticated ? 'Add a task' : 'Sign in to create tasks'} className="flex-1 rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none placeholder:text-slate-500" disabled={!authenticated} />
          <Button onClick={createTask} className="bg-gradient-to-r from-blue-500 to-violet-500 text-white" disabled={!authenticated}><Plus className="mr-2 h-4 w-4" />Create task</Button>
        </div>
      </Card>

      <Card className="p-5">
        {loading ? (
          <div className="flex items-center gap-3 text-sm text-slate-400"><Loader2 className="h-4 w-4 animate-spin" />Loading tasks from the backend...</div>
        ) : error ? (
          <div className="text-sm text-danger">{error}</div>
        ) : !authenticated ? (
          <div className="flex items-center gap-3 rounded-2xl border border-dashed border-white/10 bg-white/5 p-4 text-sm text-slate-400"><Lock className="h-4 w-4" />Sign in with Google to load your real tasks.</div>
        ) : tasks.length === 0 ? (
          <EmptyState title="No tasks yet" description="Create a task to start tracking work." />
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            {tasks.map((task) => (
              <button key={task.id} onClick={() => toggleTask(task)} className={`flex w-full items-start justify-between gap-4 rounded-2xl border border-white/10 p-4 text-left transition hover:bg-white/5 ${task.completed ? 'bg-emerald-500/10' : 'bg-white/5'}`}>
                <div className="flex min-w-0 flex-1 items-center gap-3">
                  <CheckCircle2 className={`h-4 w-4 ${task.completed ? 'text-emerald-400' : 'text-slate-400'}`} />
                  <div className="min-w-0">
                    <p className={`truncate text-sm font-medium ${task.completed ? 'text-emerald-100 line-through' : 'text-white'}`}>{task.title}</p>
                    <div className="mt-1 flex flex-wrap gap-2 text-xs text-slate-400">
                      {task.notes ? <span>{task.notes}</span> : null}
                      <span>{formatDueDate(task.due)}</span>
                    </div>
                  </div>
                </div>
                <span className={`rounded-full px-2.5 py-1 text-xs ${task.completed ? 'bg-emerald-400/10 text-emerald-200' : 'bg-white/10 text-slate-300'}`}>{task.completed ? 'Done' : 'Open'}</span>
              </button>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
