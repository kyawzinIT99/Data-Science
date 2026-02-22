"use client";

import { useState } from "react";
import { Loader2, GitCompare, Plus, X, Sparkles, TrendingUp, TrendingDown, Target } from "lucide-react";
import { useTranslations, useLocale } from "next-intl";
import { uploadFile, compareFiles, type CompareResponse, type FileUploadResponse } from "@/lib/api";

interface Props {
  primaryFileId: string;
}

export default function ComparePanel({ primaryFileId }: Props) {
  const t = useTranslations("Compare");
  const locale = useLocale();
  const [additionalFiles, setAdditionalFiles] = useState<FileUploadResponse[]>([]);
  const [uploading, setUploading] = useState(false);
  const [comparing, setComparing] = useState(false);
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [customPrompt, setCustomPrompt] = useState("");

  const handleAddFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const res = await uploadFile(file);
      setAdditionalFiles((prev) => [...prev, res]);
    } catch {
      setError(t("uploadFailed"));
    } finally {
      setUploading(false);
    }
    e.target.value = "";
  };

  const removeFile = (id: string) => {
    setAdditionalFiles((prev) => prev.filter((f) => f.file_id !== id));
  };

  const handleCompare = async () => {
    const fileIds = [primaryFileId, ...additionalFiles.map((f) => f.file_id)];
    if (fileIds.length < 2) {
      setError(t("minFiles"));
      return;
    }
    setComparing(true);
    setError(null);
    try {
      const res = await compareFiles(fileIds, customPrompt || undefined, locale);
      setResult(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || t("failed"));
    } finally {
      setComparing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload additional files */}
      <div className="glass-card p-6">
        <h3 className="text-md font-semibold mb-4 flex items-center gap-2">
          <GitCompare className="w-5 h-5 text-primary-500" />
          {t("title")}
        </h3>
        <p className="text-sm text-slate-400 mb-4">
          {t("desc")}
        </p>

        {additionalFiles.length > 0 && (
          <div className="space-y-2 mb-4">
            {additionalFiles.map((f) => (
              <div key={f.file_id} className="flex items-center justify-between bg-slate-800/50 rounded-lg p-3">
                <span className="text-sm">{f.filename}</span>
                <button onClick={() => removeFile(f.file_id)} className="p-1 hover:bg-red-500/10 rounded">
                  <X className="w-4 h-4 text-red-400" />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="flex gap-2 items-center">
          <label className="flex items-center gap-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm cursor-pointer transition">
            <Plus className="w-4 h-4" />
            {uploading ? t("uploading") : t("addFile")}
            <input type="file" onChange={handleAddFile} className="hidden" disabled={uploading} />
          </label>
        </div>

        {/* Custom prompt for comparison */}
        <div className="mt-4">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-primary-400" />
            <span className="text-xs text-slate-400">{t("customFocus")}</span>
          </div>
          <input
            type="text"
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
            placeholder={t("placeholder")}
            className="w-full bg-slate-800 rounded-lg px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 outline-none focus:ring-2 focus:ring-primary-500/50"
          />
        </div>

        <button
          onClick={handleCompare}
          disabled={additionalFiles.length === 0 || comparing}
          className="mt-4 flex items-center gap-2 px-6 py-2.5 bg-primary-600 hover:bg-primary-700 disabled:opacity-40 rounded-lg text-sm transition"
        >
          {comparing ? <Loader2 className="w-4 h-4 animate-spin" /> : <GitCompare className="w-4 h-4" />}
          {t("compareBtn", { count: additionalFiles.length + 1 })}
        </button>

        {error && <p className="text-red-400 text-sm mt-3">{error}</p>}
      </div>

      {/* Results */}
      {result && (
        <>
          {result.metrics_delta && Object.keys(result.metrics_delta).length > 0 && (
            <div className="glass-card p-6">
              <h3 className="text-md font-semibold mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-primary-400" />
                {t("performance")}
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(result.metrics_delta).map(([key, delta]) => (
                  <div key={key} className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-4">
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">{key}</p>
                    <div className="flex items-center gap-2 mt-1">
                      {delta >= 0 ? (
                        <TrendingUp className="w-4 h-4 text-green-400" />
                      ) : (
                        <TrendingDown className="w-4 h-4 text-red-400" />
                      )}
                      <span className={`text-lg font-bold ${delta >= 0 ? "text-green-400" : "text-red-400"}`}>
                        {delta > 0 ? "+" : ""}{delta}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.comparative_strategy && (
            <div className="glass-card p-6 bg-primary-500/5 border-primary-500/20">
              <h3 className="text-md font-semibold mb-3 flex items-center gap-2 text-primary-400">
                <Target className="w-5 h-5" />
                {t("aiStrategy")}
              </h3>
              <p className="text-slate-200 text-sm leading-relaxed italic">{result.comparative_strategy}</p>
            </div>
          )}

          <div className="glass-card p-6">
            <h3 className="text-md font-semibold mb-3">{t("summary")}</h3>
            <p className="text-slate-300 text-sm leading-relaxed">{result.comparison_summary}</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="glass-card p-6">
              <h3 className="text-md font-semibold mb-3 text-green-400">{t("similarities")}</h3>
              <ul className="space-y-2">
                {result.similarities.map((s, i) => (
                  <li key={i} className="flex gap-2 text-sm text-slate-300">
                    <span className="text-green-400">-</span> {s}
                  </li>
                ))}
              </ul>
            </div>
            <div className="glass-card p-6">
              <h3 className="text-md font-semibold mb-3 text-orange-400">{t("differences")}</h3>
              <ul className="space-y-2">
                {result.differences.map((d, i) => (
                  <li key={i} className="flex gap-2 text-sm text-slate-300">
                    <span className="text-orange-400">-</span> {d}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {Object.keys(result.file_summaries).length > 0 && (
            <div className="glass-card p-6">
              <h3 className="text-md font-semibold mb-3">{t("perFile")}</h3>
              <div className="space-y-2">
                {Object.entries(result.file_summaries).map(([key, summary]) => (
                  <div key={key} className="bg-slate-800/50 rounded-lg p-3">
                    <p className="text-xs text-slate-500 font-mono mb-1">Doc {key}</p>
                    <p className="text-sm text-slate-300">{summary}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
