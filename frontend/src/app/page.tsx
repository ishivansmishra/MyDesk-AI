"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function HomePage() {
  const [status, setStatus] = useState<string>("Checking backend...");

  useEffect(() => {
    api
      .health()
      .then((data) => {
        setStatus(data.status || "Backend connected");
      })
      .catch(() => {
        setStatus("Backend unavailable");
      });
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-6">
      <div className="rounded-2xl border border-slate-700 bg-slate-900 p-8 text-center">
        <h1 className="text-4xl font-bold text-white">
          MyDesk AI
        </h1>

        <p className="mt-4 text-slate-400">
          Your personal AI workspace assistant
        </p>

        <div className="mt-6 rounded-lg bg-slate-800 px-4 py-3">
          <p className="text-sm text-slate-300">
            Backend Status:
          </p>

          <p className="mt-1 text-green-400">
            {status}
          </p>
        </div>
      </div>
    </main>
  );
}