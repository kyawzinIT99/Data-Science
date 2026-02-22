"use client";

import { useState } from "react";
import { X, Link2, Copy, Check, Loader2 } from "lucide-react";
import { useTranslations } from "next-intl";
import { createShare } from "@/lib/api";

interface Props {
  fileId: string;
  onClose: () => void;
}

export default function ShareModal({ fileId, onClose }: Props) {
  const t = useTranslations("Share");
  const [includeAnalysis, setIncludeAnalysis] = useState(true);
  const [includeDashboard, setIncludeDashboard] = useState(true);
  const [expiresHours, setExpiresHours] = useState(72);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleShare = async () => {
    setLoading(true);
    try {
      const res = await createShare(fileId, includeAnalysis, includeDashboard, expiresHours);
      setShareUrl(res.share_url);
    } catch {
      alert(t("failed"));
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (shareUrl) {
      navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="glass-card p-6 w-full max-w-md">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Link2 className="w-5 h-5 text-primary-500" />
            {t("title")}
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-slate-700 rounded-lg transition">
            <X className="w-4 h-4" />
          </button>
        </div>

        {!shareUrl ? (
          <div className="space-y-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox" checked={includeAnalysis}
                onChange={(e) => setIncludeAnalysis(e.target.checked)}
                className="w-4 h-4 rounded"
              />
              <span className="text-sm">{t("includeAnalysis")}</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox" checked={includeDashboard}
                onChange={(e) => setIncludeDashboard(e.target.checked)}
                className="w-4 h-4 rounded"
              />
              <span className="text-sm">{t("includeDashboard")}</span>
            </label>
            <div>
              <label className="text-sm text-slate-400 block mb-1">{t("expiresIn")}</label>
              <select
                value={expiresHours}
                onChange={(e) => setExpiresHours(Number(e.target.value))}
                className="w-full bg-slate-800 rounded-lg px-4 py-2.5 text-sm outline-none"
              >
                <option value={24}>{t("hours24")}</option>
                <option value={72}>{t("days3")}</option>
                <option value={168}>{t("days7")}</option>
                <option value={720}>{t("days30")}</option>
              </select>
            </div>
            <button
              onClick={handleShare}
              disabled={loading || (!includeAnalysis && !includeDashboard)}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary-600 hover:bg-primary-700 disabled:opacity-40 rounded-lg text-sm transition"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Link2 className="w-4 h-4" />}
              {t("generate")}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-slate-400">{t("shareLink")}</p>
            <div className="flex gap-2">
              <input
                type="text" value={shareUrl} readOnly
                className="flex-1 bg-slate-800 rounded-lg px-4 py-2.5 text-sm text-primary-300 outline-none"
              />
              <button
                onClick={handleCopy}
                className="px-4 py-2.5 bg-slate-700 hover:bg-slate-600 rounded-lg transition"
              >
                {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-xs text-slate-500">
              {t("expiryNotice", { hours: expiresHours })}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
