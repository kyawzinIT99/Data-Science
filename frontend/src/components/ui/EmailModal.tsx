"use client";

import { useState } from "react";
import { X, Mail, Loader2, Check } from "lucide-react";
import { useTranslations } from "next-intl";
import { emailReport } from "@/lib/api";

interface Props {
  fileId: string;
  onClose: () => void;
}

export default function EmailModal({ fileId, onClose }: Props) {
  const t = useTranslations("Email");
  const [email, setEmail] = useState("");
  const [includeCharts, setIncludeCharts] = useState(true);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSend = async () => {
    if (!email.trim()) return;
    setSending(true);
    setError(null);
    try {
      await emailReport(fileId, email.trim(), includeCharts);
      setSent(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || t("failed"));
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="glass-card p-6 w-full max-w-md">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Mail className="w-5 h-5 text-primary-500" />
            {t("title")}
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-slate-700 rounded-lg transition">
            <X className="w-4 h-4" />
          </button>
        </div>

        {sent ? (
          <div className="text-center py-6">
            <Check className="w-10 h-10 text-green-400 mx-auto mb-3" />
            <p className="text-green-400 font-medium">{t("sent")}</p>
            <p className="text-sm text-slate-500 mt-1">{t("sentSub", { email })}</p>
            <button onClick={onClose} className="mt-4 px-6 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm transition">
              {t("close")}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="text-sm text-slate-400 block mb-1">{t("recipient")}</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder="colleague@example.com"
                className="w-full bg-slate-800 rounded-lg px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 outline-none focus:ring-2 focus:ring-primary-500/50"
              />
            </div>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={includeCharts}
                onChange={(e) => setIncludeCharts(e.target.checked)}
                className="w-4 h-4 rounded"
              />
              <span className="text-sm">{t("includeCharts")}</span>
            </label>
            {error && (
              <p className="text-sm text-red-400 bg-red-500/10 rounded-lg p-2">{error}</p>
            )}
            <button
              onClick={handleSend}
              disabled={!email.trim() || sending}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary-600 hover:bg-primary-700 disabled:opacity-40 rounded-lg text-sm transition"
            >
              {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mail className="w-4 h-4" />}
              {t("send")}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
