"use client";

import { useState, useEffect } from "react";
import { Loader2, Lightbulb, TrendingUp, CheckCircle2, BarChart3, RefreshCw, Sparkles } from "lucide-react";
import { useTranslations, useLocale } from "next-intl";
import { analyzeFile, type AnalysisResponse } from "@/lib/api";

export default function AnalysisPanel({ fileId }: { fileId: string }) {
  const t = useTranslations("Analysis");
  const locale = useLocale();
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [customPrompt, setCustomPrompt] = useState("");
  const [showPrompt, setShowPrompt] = useState(false);

  const runAnalysis = async (prompt?: string) => {
    setLoading(true);
    setError(null);

    const MAX_RETRIES = 2;
    let lastErr: any = null;

    for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
      try {
        if (attempt > 0) {
          console.log(`[AnalysisPanel] Retry attempt ${attempt}/${MAX_RETRIES}...`);
          await new Promise(r => setTimeout(r, 1500 * attempt));
        }
        const data = await analyzeFile(fileId, prompt, locale);
        setAnalysis(data);
        setLoading(false);
        return;
      } catch (err: any) {
        lastErr = err;
        const status = err?.response?.status;
        if (status === 500 && attempt < MAX_RETRIES) {
          console.warn(`[AnalysisPanel] Got 500, retrying (${attempt + 1}/${MAX_RETRIES})...`);
          continue;
        }
        break;
      }
    }

    setError(lastErr?.response?.data?.detail || t("failed"));
    setLoading(false);
  };

  useEffect(() => {
    runAnalysis();
  }, [fileId]);

  const handleCustomAnalysis = () => {
    if (!customPrompt.trim()) return;
    runAnalysis(customPrompt.trim());
    setShowPrompt(false);
  };

  if (loading) {
    return (
      <div className="glass-card p-12 text-center">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin mx-auto mb-4" />
        <p className="text-slate-400">{t("loading")}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card p-8 text-center text-red-400">
        <p>{error}</p>
      </div>
    );
  }

  if (!analysis) return null;

  return (
    <div className="space-y-6">
      {/* Custom prompt bar */}
      <div className="glass-card p-4">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowPrompt(!showPrompt)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm transition ${showPrompt ? "bg-primary-600/20 text-primary-300" : "hover:bg-slate-800 text-slate-400"
              }`}
          >
            <Sparkles className="w-4 h-4" />
            {t("customFocus")}
          </button>
          <button
            onClick={() => runAnalysis()}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm hover:bg-slate-800 text-slate-400 transition"
          >
            <RefreshCw className="w-4 h-4" />
            {t("reAnalyze")}
          </button>
        </div>
        {showPrompt && (
          <div className="mt-3 flex gap-2">
            <input
              type="text"
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCustomAnalysis()}
              placeholder={t("promptPlaceholder")}
              className="flex-1 bg-slate-800 rounded-lg px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 outline-none focus:ring-2 focus:ring-primary-500/50"
            />
            <button
              onClick={handleCustomAnalysis}
              disabled={!customPrompt.trim()}
              className="px-4 py-2.5 bg-primary-600 hover:bg-primary-700 disabled:opacity-40 rounded-lg text-sm transition"
            >
              {t("analyze")}
            </button>
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-primary-500" />
          {t("summary")}
        </h2>
        <p className="text-slate-300 leading-relaxed">{analysis.summary}</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="glass-card p-6">
          <h3 className="text-md font-semibold mb-3 flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-yellow-400" />
            {t("keyInsights")}
          </h3>
          <ul className="space-y-2">
            {analysis.key_insights.map((insight, i) => (
              <li key={i} className="flex gap-2 text-sm text-slate-300">
                <span className="text-yellow-400 mt-0.5">-</span>
                {insight}
              </li>
            ))}
          </ul>
        </div>

        <div className="glass-card p-6">
          <h3 className="text-md font-semibold mb-3 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-400" />
            {t("trends")}
          </h3>
          <ul className="space-y-2">
            {analysis.trends.map((trend, i) => (
              <li key={i} className="flex gap-2 text-sm text-slate-300">
                <span className="text-green-400 mt-0.5">-</span>
                {trend}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="glass-card p-6">
        <h3 className="text-md font-semibold mb-3 flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-purple-400" />
          {t("recommendations")}
        </h3>
        <ul className="space-y-2">
          {analysis.recommendations.map((rec, i) => (
            <li key={i} className="flex gap-2 text-sm text-slate-300">
              <span className="text-purple-400 mt-0.5">{i + 1}.</span>
              {rec}
            </li>
          ))}
        </ul>
      </div>

      {analysis.data_stats && (
        <div className="glass-card p-6">
          <h3 className="text-md font-semibold mb-3">{t("dataStats")}</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(analysis.data_stats).map(([key, val]) => (
              <div key={key} className="bg-slate-800/50 rounded-lg p-3">
                <p className="text-xs text-slate-500 capitalize">{key.replace(/_/g, " ")}</p>
                <p className="text-lg font-semibold mt-1">
                  {typeof val === "object" ? Object.keys(val).length : String(val)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
