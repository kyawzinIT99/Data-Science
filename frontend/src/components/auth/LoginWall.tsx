"use client";

import React, { useState, useEffect } from "react";
import { login } from "@/lib/api";

export default function LoginWall({ children }: { children: React.ReactNode }) {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem("kyawzin_access_token");
        // Ensure we are checking for the latest version of the token
        if (token === "kyawzin_cloud_access_v4") {
            setIsAuthenticated(true);
        } else {
            setIsAuthenticated(false);
        }
    }, []);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError("");
        try {
            await login(username, password);
            setIsAuthenticated(true);
        } catch (err: any) {
            setError("Invalid username or password");
        } finally {
            setIsLoading(false);
        }
    };

    // Prevent flash of login screen while checking local storage
    if (isAuthenticated === null) {
        return <div className="fixed inset-0 bg-slate-900 z-[9999]" />;
    }

    // If this is a shared report link, bypass the login wall
    // Note: This relies on the URL structure. Shared links are served via /shared/[id] 
    // but in Next.js localized structure it might be /[locale]/shared/... 
    // Actually, we saw /shared in main.py catch-all.
    if (typeof window !== "undefined" && (window.location.pathname.includes("/shared") || window.location.pathname.includes("/shared/"))) {
        return <>{children}</>;
    }

    if (isAuthenticated) {
        return <>{children}</>;
    }

    return (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-slate-950/95 backdrop-blur-xl">
            <div className="w-full max-w-md p-8 bg-slate-900/50 backdrop-blur-md border border-slate-800 rounded-3xl shadow-2xl">
                <div className="text-center mb-10">
                    <div className="w-20 h-20 bg-indigo-600/20 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-indigo-500/30">
                        <svg className="w-10 h-10 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                    </div>
                    <h1 className="text-3xl font-extrabold text-white tracking-tight">Access Control</h1>
                    <p className="text-slate-400 mt-2">Sign in to the analytics dashboard</p>
                </div>

                <form onSubmit={handleLogin} className="space-y-5">
                    <div>
                        <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 ml-1">Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full px-5 py-4 bg-slate-950/50 border border-slate-800 rounded-2xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all placeholder:text-slate-700"
                            placeholder="kyawzin"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 ml-1">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-5 py-4 bg-slate-950/50 border border-slate-800 rounded-2xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all placeholder:text-slate-700"
                            placeholder="••••••••"
                            required
                        />
                    </div>

                    {error && (
                        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-500 text-sm font-medium animate-shake text-center">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-2xl transition-all shadow-[0_0_20px_rgba(79,70,229,0.3)] disabled:opacity-50 active:scale-[0.98]"
                    >
                        {isLoading ? (
                            <span className="flex items-center justify-center gap-2">
                                <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Processing...
                            </span>
                        ) : "Authenticate"}
                    </button>
                </form>

                <div className="mt-10 mb-2 pt-6 border-t border-slate-800 text-center">
                    <p className="text-[10px] items-center justify-center flex gap-1 text-slate-600 font-medium uppercase tracking-[0.2em]">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                        Professional Tier Security
                    </p>
                </div>
            </div>
        </div>
    );
}
