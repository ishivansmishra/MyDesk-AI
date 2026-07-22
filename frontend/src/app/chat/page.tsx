"use client";

import { useEffect, useState } from 'react';
import { ArrowUp, Mic, Paperclip, Sparkles, RefreshCw, Copy, Bot, Lock, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';

const CHAT_STORAGE_KEY = 'mydesk-chat-history';
const suggestions = ['Plan my day', 'Add a task', 'Schedule a meeting'];

type Message = {
  role: 'assistant' | 'user';
  content: string;
  result?: Record<string, unknown> | null;
};

type SpeechRecognitionLike = {
  lang: string;
  interimResults: boolean;
  onstart: (() => void) | null;
  onerror: ((event: Event) => void) | null;
  onend: (() => void) | null;
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  start: () => void;
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem(CHAT_STORAGE_KEY);
    if (stored) {
      try {
        setMessages(JSON.parse(stored) as Message[]);
      } catch {
        window.localStorage.removeItem(CHAT_STORAGE_KEY);
      }
    }
    setAuthenticated(Boolean(window.localStorage.getItem('mydesk-auth-token')));
  }, []);

  useEffect(() => {
    if (messages.length > 0) {
      window.localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
    } else {
      window.localStorage.removeItem(CHAT_STORAGE_KEY);
    }
  }, [messages]);

  const handleSuggestion = async (suggestion: string) => {
    if (!authenticated) return;
    setInput(suggestion);
    await handleSend(suggestion);
  };

  const handleVoiceInput = () => {
    if (!authenticated) return;
    if (typeof window === 'undefined') return;
    const speechApi = window as typeof window & {
      SpeechRecognition?: new () => SpeechRecognitionLike;
      webkitSpeechRecognition?: new () => SpeechRecognitionLike;
    };
    const SpeechRecognition = speechApi.SpeechRecognition || speechApi.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setMessages((current) => [...current, { role: 'assistant', content: 'Speech input is not supported in this browser.' }]);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.onstart = () => setIsListening(true);
    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);
    recognition.onresult = (event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => {
      const transcript = Array.from(event.results).map((result) => result[0].transcript).join(' ');
      setInput(transcript);
      void handleSend(transcript);
    };
    recognition.start();
  };

  const handleSend = async (messageText?: string) => {
    const trimmed = (messageText ?? input).trim();
    if (!trimmed) return;

    const userMessage: Message = { role: 'user', content: trimmed };
    setMessages((current) => [...current, userMessage]);
    setInput('');
    setIsSending(true);

    try {
      const response = await api.chat({ message: trimmed });
      setMessages((current) => [...current, { role: 'assistant', content: response.reply, result: response.result ?? null }]);
    } catch (error) {
      setMessages((current) => [...current, { role: 'assistant', content: error instanceof Error ? error.message : 'Unable to reach the assistant right now.' }]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="rounded-[24px] border border-white/10 bg-slate-950/70 p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-400">AI Assistant</p>
            <h1 className="text-2xl font-semibold text-white">Chat with MyDesk AI</h1>
          </div>
          <div className={`rounded-full px-3 py-1 text-sm ${authenticated ? 'border border-emerald-400/20 bg-emerald-500/10 text-emerald-300' : 'border border-slate-700 bg-slate-800 text-slate-300'}`}>
            {authenticated ? 'Live • connected' : 'Sign in required'}
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden rounded-[24px] border border-white/10 bg-[rgba(17,24,39,0.85)] p-4">
        <div className="flex h-full flex-col">
          <div className="flex-1 space-y-3 overflow-y-auto pr-2">
            {!authenticated ? (
              <div className="flex h-full items-center justify-center rounded-[20px] border border-dashed border-white/10 bg-white/5 p-6 text-center">
                <div>
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-500/10 text-blue-200">
                    <Lock className="h-5 w-5" />
                  </div>
                  <p className="mt-4 text-lg font-semibold text-white">Sign in with Google to start using your AI Workspace Assistant.</p>
                  <p className="mt-2 text-sm text-slate-400">Chat, voice, and workflow automation unlock after authentication.</p>
                </div>
              </div>
            ) : messages.length === 0 ? (
              <div className="flex h-full items-center justify-center rounded-[20px] border border-dashed border-white/10 bg-white/5 p-6 text-center text-sm text-slate-400">
                Start a conversation and your workspace insights will appear here.
              </div>
            ) : null}
            {messages.map((message, index) => (
              <div key={`${message.role}-${index}`} className={`flex ${message.role === 'assistant' ? 'justify-start' : 'justify-end'}`}>
                <div className={`max-w-[80%] rounded-3xl px-4 py-3 ${message.role === 'assistant' ? 'bg-white/10 text-slate-100' : 'bg-gradient-to-r from-blue-500 to-violet-500 text-white'}`}>
                  <div className="mb-2 flex items-center gap-2 text-xs uppercase tracking-[0.24em] text-slate-300/80">
                    {message.role === 'assistant' ? <Bot className="h-3.5 w-3.5" /> : <Sparkles className="h-3.5 w-3.5" />}
                    {message.role === 'assistant' ? 'MyDesk AI' : 'You'}
                  </div>
                  <p className="text-sm leading-7">{message.content}</p>
                  {message.result ? (
                    <pre className="mt-3 overflow-x-auto rounded-2xl bg-slate-900/90 p-3 text-xs text-slate-300">
                      {JSON.stringify(message.result, null, 2)}
                    </pre>
                  ) : null}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 rounded-[24px] border border-white/10 bg-slate-900/90 p-3">
            <div className="flex flex-wrap gap-2">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => void handleSuggestion(suggestion)}
                  className="rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300 transition hover:bg-white/10"
                >
                  {suggestion}
                </button>
              ))}
            </div>
            <div className="mt-3 flex items-center gap-2 rounded-2xl border border-white/10 bg-slate-950/70 p-2">
              <button className="rounded-xl border border-white/10 bg-white/5 p-2 text-slate-300 transition hover:bg-white/10">
                <Paperclip className="h-4 w-4" />
              </button>
              <input
                className="flex-1 bg-transparent px-2 py-2 text-sm text-slate-100 outline-none placeholder:text-slate-500"
                placeholder={authenticated ? 'Ask anything about your workspace...' : 'Sign in to chat'}
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && authenticated) {
                    void handleSend();
                  }
                }}
                disabled={!authenticated}
              />
              <button className="rounded-xl border border-white/10 bg-white/5 p-2 text-slate-300 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-60" disabled={!authenticated} onClick={() => handleVoiceInput()}>
                {isListening ? <Loader2 className="h-4 w-4 animate-spin" /> : <Mic className="h-4 w-4" />}
              </button>
              <button
                className="rounded-xl bg-gradient-to-r from-blue-500 to-violet-500 p-2 text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                onClick={() => void handleSend()}
                disabled={isSending || !authenticated}
              >
                <ArrowUp className="h-4 w-4" />
              </button>
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
              <span>Press Enter to send</span>
              <div className="flex items-center gap-2">
                <button className="rounded-full border border-white/10 bg-white/5 p-2">
                  <Copy className="h-3.5 w-3.5" />
                </button>
                <button className="rounded-full border border-white/10 bg-white/5 p-2">
                  <RefreshCw className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
