"use client";

import { useState, useEffect } from "react";
import { Loader2, AlertTriangle, CheckCircle, Info, Shield } from "lucide-react";
import { useTranslations } from "next-intl";
import { getDataCleaning, type DataCleaningResponse } from "@/lib/api";

const severityColors: Record<string, string> = {
  high: "text-red-400 bg-red-500/10 border-red-500/20",
  medium: "text-yellow-400 bg-yellow-500/10 border-yellow-500/20",
  low: "text-blue-400 bg-blue-500/10 border-blue-500/20",
};

export default function CleaningPanel({ fileId }: { fileId: string }) {
  const t = useTranslations("Cleaning");
  const [data, setData] = useState<DataCleaningResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const issueTypeLabels: Record<string, string> = {
    missing_values: t("missing"),
    duplicates: t("duplicates"),
    outliers: t("outliers"),
    type_mismatch: t("typeMismatch"),
    formatting: t("formatting"),
  };

  useEffect(() => {
    setLoading(true);
    getDataCleaning(fileId)
      .then(setData)
      .catch((err) => setError(err.response?.data?.detail || t("failed")))
      .finally(() => setLoading(false));
  }, [fileId]);

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
      <div className="glass-card p-8 text-center text-yellow-400">
        <Info className="w-8 h-8 mx-auto mb-3 opacity-60" />
        <p>{error}</p>
      </div>
    );
  }

  if (!data) return null;

  const scoreColor = data.quality_score >= 80 ? "text-green-400" : data.quality_score >= 50 ? "text-yellow-400" : "text-red-400";

  return (
    <div className="space-y-6">
      {/* Quality Score */}
      <div className="glass-card p-6 flex items-center gap-6">
        <div className="text-center">
          <div className={`text-4xl font-bold ${scoreColor}`}>{data.quality_score}%</div>
          <p className="text-xs text-slate-500 mt-1">{t("qualityScore")}</p>
        </div>
        <div className="flex-1 grid grid-cols-3 gap-4">
          <div className="bg-slate-800/50 rounded-lg p-3 text-center">
            <p className="text-lg font-semibold">{data.total_issues}</p>
            <p className="text-xs text-slate-500">{t("totalIssues")}</p>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-3 text-center">
            <p className="text-lg font-semibold text-red-400">
              {data.issues.filter((i) => i.severity === "high").length}
            </p>
            <p className="text-xs text-slate-500">{t("critical")}</p>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-3 text-center">
            <p className="text-lg font-semibold text-yellow-400">
              {data.issues.filter((i) => i.severity === "medium").length}
            </p>
            <p className="text-xs text-slate-500">{t("warnings")}</p>
          </div>
        </div>
      </div>

      {/* Issues */}
      {data.issues.length > 0 && (
        <div className="glass-card p-6">
          <h3 className="text-md font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            {t("issuesFound")}
          </h3>
          <div className="space-y-3">
            {data.issues.map((issue, i) => (
              <div key={i} className={`border rounded-lg p-4 ${severityColors[issue.severity]}`}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium">
                    {issueTypeLabels[issue.issue_type] || issue.issue_type} — <code className="text-xs">{issue.column}</code>
                  </span>
                  <span className="text-xs uppercase font-medium px-2 py-0.5 rounded-full bg-current/10">
                    {issue.severity}
                  </span>
                </div>
                <p className="text-sm opacity-80">{issue.description}</p>
                <p className="text-xs mt-2 opacity-60">{issue.suggestion}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Recommendations */}
      {data.ai_recommendations.length > 0 && (
        <div className="glass-card p-6">
          <h3 className="text-md font-semibold mb-3 flex items-center gap-2">
            <Shield className="w-5 h-5 text-green-400" />
            {t("aiRecs")}
          </h3>
          <ul className="space-y-2">
            {data.ai_recommendations.map((rec, i) => (
              <li key={i} className="flex gap-2 text-sm text-slate-300">
                <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 shrink-0" />
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
