"use client";

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const connected = params.get('connected') === '1';
    const token = params.get('token');
    if (token) {
      window.localStorage.setItem('mydesk-auth-token', token);
      router.replace('/');
    }
    if (connected && !token) {
      setError('Authentication callback did not return a valid token.');
    }
  }, [router]);

  const handleGoogleSignIn = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.startGoogleOAuth('/login');
      if (response.authorization_url) {
        window.location.href = response.authorization_url;
      } else {
        setError('Google OAuth is not configured.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to initiate Google sign-in.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-[70vh] max-w-2xl items-center justify-center px-4">
      <Card className="w-full p-8">
        <div className="text-center">
          <p className="text-sm text-slate-400">Secure access</p>
          <h1 className="mt-2 text-3xl font-semibold text-white">Sign in with Google</h1>
          <p className="mt-3 text-sm leading-7 text-slate-400">Authenticate with your Google account to access calendar, tasks, chat, and workspace automation.</p>
        </div>

        <div className="mt-8 space-y-4">
          {error ? <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-3 text-sm text-rose-300">{error}</div> : null}
          <Button onClick={handleGoogleSignIn} disabled={loading} className="w-full bg-gradient-to-r from-blue-500 to-violet-500 text-white">
            {loading ? 'Redirecting to Google…' : 'Continue with Google'}
          </Button>
          <p className="text-xs text-slate-500">Google OAuth is the only authentication method supported.</p>
        </div>
      </Card>
    </div>
  );
}
