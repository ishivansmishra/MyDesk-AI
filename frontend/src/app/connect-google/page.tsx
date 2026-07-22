"use client";

import { useEffect, useState } from 'react';
import { ArrowRight, CheckCircle2, Loader2, PlugZap, RefreshCw, Unplug } from 'lucide-react';
import { api } from '@/lib/api';

export default function ConnectGooglePage() {
  const [status, setStatus] = useState<'loading' | 'connected' | 'disconnected' | 'error'>('loading');
  const [profile, setProfile] = useState<{ email?: string; connected?: boolean; configured?: boolean } | null>(null);

  const loadStatus = async () => {
    try {
      const response = await api.getGoogleStatus();
      setProfile(response);
      setStatus(response.connected ? 'connected' : 'disconnected');
    } catch (error) {
      setStatus('error');
      setProfile({ connected: false, configured: false });
      console.error(error);
    }
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const connected = params.get('connected') === '1';
    const token = params.get('token');

    if (token) {
      console.debug('Connect Google callback token received, storing auth token');
      window.localStorage.setItem('mydesk-auth-token', token);
    }

    if (connected) {
      console.debug('Connect Google callback indicated successful connection');
      setStatus('connected');
      setProfile((current) => ({ ...(current || {}), connected: true, configured: true }));
    }

    void loadStatus();
  }, []);

  const connect = async () => {
    try {
      await api.startGoogleOAuth('/connect-google');
    } catch (error) {
      setStatus('error');
      console.error(error);
    }
  };

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <div className="rounded-[28px] border border-white/10 bg-slate-950/70 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm text-slate-400">Google Workspace</p>
            <h1 className="text-2xl font-semibold text-white">Connect Google Workspace</h1>
          </div>
          <div className={`rounded-full px-3 py-1 text-sm ${status === 'connected' ? 'bg-emerald-500/10 text-emerald-300' : status === 'error' ? 'bg-rose-500/10 text-rose-300' : 'bg-slate-800 text-slate-300'}`}>
            {status === 'connected' ? 'Connected' : status === 'error' ? 'Needs attention' : 'Checking connection'}
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-[28px] border border-white/10 bg-[rgba(17,24,39,0.85)] p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-violet-500">
              <PlugZap className="h-6 w-6 text-white" />
            </div>
            <div>
              <p className="text-lg font-semibold text-white">Google account access</p>
              <p className="text-sm text-slate-400">Enable Calendar, Tasks, and Gmail workflows with your real Google account.</p>
            </div>
          </div>

          <div className="mt-6 rounded-2xl border border-white/10 bg-slate-900/70 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Connection status</p>
                <p className="font-medium text-white">{status === 'connected' ? 'Connected Google account' : 'Not connected yet'}</p>
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-300">
                {status === 'loading' ? <Loader2 className="h-4 w-4 animate-spin" /> : status === 'connected' ? <CheckCircle2 className="h-4 w-4 text-emerald-400" /> : <RefreshCw className="h-4 w-4" />}
                {status === 'connected' ? 'Ready' : 'Pending'}
              </div>
            </div>
            {profile?.email ? (
              <div className="mt-4 rounded-xl border border-emerald-400/20 bg-emerald-500/10 p-3 text-sm text-emerald-200">
                <p className="font-medium">{profile.email}</p>
              </div>
            ) : null}
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <button onClick={connect} className="inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-blue-500 to-violet-500 px-4 py-3 font-medium text-white transition hover:opacity-90">
              <PlugZap className="h-4 w-4" />
              Connect Google Workspace
            </button>
            <button onClick={() => void loadStatus()} className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300">
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
          </div>
        </div>

        <div className="rounded-[28px] border border-white/10 bg-slate-950/70 p-6">
          <p className="text-sm font-medium text-slate-300">What this enables</p>
          <ul className="mt-4 space-y-3 text-sm text-slate-400">
            <li>• Real Google Calendar CRUD</li>
            <li>• Real Google Tasks CRUD</li>
            <li>• Secure token storage and reconnect support</li>
            <li>• Automatic workspace-aware AI actions</li>
          </ul>
          <div className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-400">
            <p className="font-medium text-white">Security note</p>
            <p className="mt-2">Authentication stays server-side and uses the credentials from your environment file.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
