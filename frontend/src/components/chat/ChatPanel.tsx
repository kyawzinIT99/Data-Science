"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Bot, User, MessageSquarePlus, History, Trash2 } from "lucide-react";
import { useTranslations, useLocale } from "next-intl";
import { chatWithFile, getChatSessions, deleteChatSession, type ChatSessionInfo } from "@/lib/api";
import ReactMarkdown from "react-markdown";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPanel({ fileId }: { fileId: string }) {
  const t = useTranslations("Chat");
  const locale = useLocale();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [sessions, setSessions] = useState<ChatSessionInfo[]>([]);
  const [showSessions, setShowSessions] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    getChatSessions(fileId).then(setSessions).catch(() => { });
  }, [fileId]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const question = input.trim();
    setInput("");
    const userMsg: Message = { role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await chatWithFile(fileId, question, messages, sessionId, locale);
      setSessionId(res.session_id);
      setMessages((prev) => [...prev, { role: "assistant", content: res.answer }]);
      // Refresh sessions list
      getChatSessions(fileId).then(setSessions).catch(() => { });
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: t("error") },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const startNewSession = () => {
    setMessages([]);
    setSessionId(undefined);
    setShowSessions(false);
  };

  const loadSession = (s: ChatSessionInfo) => {
    setSessionId(s.session_id);
    setMessages(s.messages.map((m) => ({ role: m.role as "user" | "assistant", content: m.content })));
    setShowSessions(false);
  };

  const handleDeleteSession = async (sid: string) => {
    await deleteChatSession(sid);
    setSessions((prev) => prev.filter((s) => s.session_id !== sid));
    if (sessionId === sid) startNewSession();
  };

  return (
    <div className="flex gap-4" style={{ height: "65vh" }}>
      {/* Sessions sidebar */}
      {showSessions && (
        <div className="w-64 glass-card p-4 flex flex-col shrink-0">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-slate-400">{t("history")}</h3>
            <button onClick={startNewSession} className="p-1.5 hover:bg-slate-700 rounded-lg transition" title={t("newChat")}>
              <MessageSquarePlus className="w-4 h-4 text-primary-400" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto space-y-1">
            {sessions.length === 0 && (
              <p className="text-xs text-slate-600 text-center mt-4">{t("noSessions")}</p>
            )}
            {sessions.map((s) => (
              <div
                key={s.session_id}
                onClick={() => loadSession(s)}
                className={`p-2 rounded-lg text-xs cursor-pointer flex items-center justify-between group transition ${sessionId === s.session_id ? "bg-primary-600/20 text-primary-300" : "hover:bg-slate-800 text-slate-400"
                  }`}
              >
                <span className="truncate flex-1">{s.title}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDeleteSession(s.session_id); }}
                  className="p-1 hover:bg-red-500/10 rounded opacity-0 group-hover:opacity-100 transition"
                >
                  <Trash2 className="w-3 h-3 text-red-400" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main chat area */}
      <div className="glass-card flex flex-col flex-1">
        {/* Toolbar */}
        <div className="flex items-center gap-2 p-3 border-b border-slate-800">
          <button
            onClick={() => setShowSessions(!showSessions)}
            className={`p-2 rounded-lg transition text-sm flex items-center gap-1.5 ${showSessions ? "bg-primary-600/20 text-primary-300" : "hover:bg-slate-800 text-slate-400"
              }`}
          >
            <History className="w-4 h-4" />
            {t("sessions")}
          </button>
          <button
            onClick={startNewSession}
            className="p-2 hover:bg-slate-800 rounded-lg transition text-slate-400 text-sm flex items-center gap-1.5"
          >
            <MessageSquarePlus className="w-4 h-4" />
            {t("newChat")}
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-slate-500 mt-20">
              <Bot className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>{t("emptyState")}</p>
              <p className="text-xs mt-1">{t("emptyStateSub")}</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-lg bg-primary-600/20 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 text-primary-400" />
                </div>
              )}
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm ${msg.role === "user" ? "bg-primary-600 text-white" : "bg-slate-800 text-slate-200"
                  }`}
              >
                {msg.role === "assistant" ? (
                  <ReactMarkdown className="prose prose-invert prose-sm max-w-none">{msg.content}</ReactMarkdown>
                ) : (
                  msg.content
                )}
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-lg bg-slate-700 flex items-center justify-center shrink-0">
                  <User className="w-4 h-4 text-slate-400" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary-600/20 flex items-center justify-center">
                <Bot className="w-4 h-4 text-primary-400" />
              </div>
              <div className="bg-slate-800 rounded-2xl px-4 py-3">
                <Loader2 className="w-4 h-4 animate-spin text-primary-400" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-slate-800">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder={t("placeholder")}
              className="flex-1 bg-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder:text-slate-500 outline-none focus:ring-2 focus:ring-primary-500/50"
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="px-4 py-3 bg-primary-600 hover:bg-primary-700 disabled:opacity-40 rounded-xl transition"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
