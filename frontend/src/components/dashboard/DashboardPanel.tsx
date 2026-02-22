"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Loader2, Download, GripVertical, TrendingUp, TrendingDown, DollarSign, Target, Lightbulb, ArrowUpRight, CheckCircle2, Zap, AlertTriangle, ShieldCheck, Share2, Copy, Check } from "lucide-react";
import { useTranslations, useLocale } from "next-intl";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  AreaChart, Area, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  rectSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { getDashboard, getCausalNetwork, checkDataQuality, refineDataset, createShare, type DashboardResponse, type ChartData, type CausalNetwork, type QAResponse } from "@/lib/api";
import dynamic from 'next/dynamic';

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

const COLORS = ["#3b82f6", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981", "#6366f1"];

function RenderChart({ chart }: { chart: ChartData }) {
  const data = chart.data;

  switch (chart.chart_type) {
    case "bar":
      return (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="label" stroke="#94a3b8" fontSize={12} />
            <YAxis stroke="#94a3b8" fontSize={12} />
            <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px" }} />
            <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      );

    case "line":
      return (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="label" stroke="#94a3b8" fontSize={12} />
            <YAxis stroke="#94a3b8" fontSize={12} />
            <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px" }} />
            <Line type="monotone" dataKey="value" stroke="#8b5cf6" strokeWidth={2} dot={{ fill: "#8b5cf6" }} />
          </LineChart>
        </ResponsiveContainer>
      );

    case "pie":
      return (
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="label" cx="50%" cy="50%" outerRadius={100} label>
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px" }} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      );

    case "area":
      return (
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="label" stroke="#94a3b8" fontSize={12} />
            <YAxis stroke="#94a3b8" fontSize={12} />
            <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px" }} />
            <Area type="monotone" dataKey="value" stroke="#ec4899" fill="#ec4899" fillOpacity={0.2} />
          </AreaChart>
        </ResponsiveContainer>
      );

    case "scatter":
      return (
        <ResponsiveContainer width="100%" height={300}>
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="x" stroke="#94a3b8" fontSize={12} name={chart.x_axis || "X"} />
            <YAxis dataKey="y" stroke="#94a3b8" fontSize={12} name={chart.y_axis || "Y"} />
            <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px" }} />
            <Scatter data={data} fill="#10b981" />
          </ScatterChart>
        </ResponsiveContainer>
      );

    default:
      return (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="label" stroke="#94a3b8" fontSize={12} />
            <YAxis stroke="#94a3b8" fontSize={12} />
            <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px" }} />
            <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      );
  }
}

function TimeDecompositionChart({ decomposition }: { decomposition: NonNullable<DashboardResponse["time_series_decomposition"]> }) {
  const [activeTab, setActiveTab] = useState<"trend" | "seasonal" | "residual">("trend");
  const t = useTranslations("Dashboard");

  const data = decomposition.dates.map((date, i) => ({
    date,
    observed: decomposition.observed[i],
    trend: decomposition.trend[i],
    seasonal: decomposition.seasonal[i],
    residual: decomposition.residual[i],
  }));

  const colors = {
    observed: "#94a3b8",
    trend: "#3b82f6",
    seasonal: "#10b981",
    residual: "#f59e0b",
  };

  return (
    <div className="glass-card p-6 border-t-2 border-primary-500/50">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-primary-400" />
          <h3 className="font-semibold text-slate-200">{t("timeSeriesDecomposition") || "Time-Series Decomposition"}</h3>
          <span className="ml-2 px-2 py-0.5 bg-primary-500/10 border border-primary-500/20 rounded-full text-[10px] font-mono text-primary-400 uppercase tracking-widest">
            MODEL: PROPHET
          </span>
        </div>
        <div className="flex bg-slate-800/50 p-1 rounded-lg border border-slate-700/50">
          {(["trend", "seasonal", "residual"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all capitalize ${activeTab === tab
                ? "bg-primary-600 text-white shadow-lg"
                : "text-slate-400 hover:text-slate-200"
                }`}
            >
              {tab === "trend" ? "Trend" : tab === "seasonal" ? "Seasonality" : "Residuals"}
            </button>
          ))}
        </div>
      </div>

      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="date" stroke="#94a3b8" fontSize={10} minTickGap={30} />
            <YAxis stroke="#94a3b8" fontSize={10} />
            <Tooltip
              contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px" }}
              itemStyle={{ fontSize: "12px" }}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="observed"
              stroke={colors.observed}
              fill="transparent"
              name="Observed"
              strokeDasharray="5 5"
            />
            <Area
              type="monotone"
              dataKey={activeTab}
              stroke={colors[activeTab]}
              fill={colors[activeTab]}
              fillOpacity={0.1}
              name={activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
              strokeWidth={3}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <p className="text-[11px] text-slate-500 mt-4 text-center">
        {activeTab === "trend" && "The trend shows the long-term direction of the data, smoothing out short-term fluctuations."}
        {activeTab === "seasonal" && "Seasonality captures recurring patterns or cycles within the data (e.g., weekly or monthly)."}
        {activeTab === "residual" && "Residuals are the remaining noise after trend and seasonality are removed, often highlighting unexpected shocks."}
      </p>
    </div>
  );
}

function SortableChartCard({ chart, id }: { chart: ChartData; id: string }) {
  const chartRef = useRef<HTMLDivElement>(null);
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const downloadChart = useCallback(() => {
    if (!chartRef.current) return;
    const svg = chartRef.current.querySelector("svg");
    if (!svg) return;

    const svgData = new XMLSerializer().serializeToString(svg);
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    const img = new window.Image();

    img.onload = () => {
      canvas.width = img.width * 2;
      canvas.height = img.height * 2;
      ctx!.fillStyle = "#1e293b";
      ctx!.fillRect(0, 0, canvas.width, canvas.height);
      ctx!.scale(2, 2);
      ctx!.drawImage(img, 0, 0);
      const link = document.createElement("a");
      link.download = `${chart.title.replace(/\s+/g, "_")}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
    };
    img.src = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(svgData)));
  }, [chart.title]);

  return (
    <div ref={setNodeRef} style={style} className="glass-card p-6">
      <div className="flex items-start justify-between mb-1">
        <div className="flex items-start gap-2 flex-1 min-w-0">
          <button
            {...attributes}
            {...listeners}
            className="p-1 mt-0.5 hover:bg-slate-700 rounded cursor-grab active:cursor-grabbing text-slate-500 hover:text-slate-300 transition"
          >
            <GripVertical className="w-4 h-4" />
          </button>
          <div className="min-w-0">
            <h3 className="font-semibold">{chart.title}</h3>
            <p className="text-xs text-slate-500 mb-4">{chart.description}</p>
          </div>
        </div>
        <button
          onClick={downloadChart}
          className="p-2 hover:bg-slate-700 rounded-lg transition text-slate-400 hover:text-white"
        >
          <Download className="w-4 h-4" />
        </button>
      </div>
      <div ref={chartRef}>
        <RenderChart chart={chart} />
      </div>
    </div>
  );
}

export default function DashboardPanel({ fileId }: { fileId: string }) {
  const t = useTranslations("Dashboard");
  const locale = useLocale();
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [causal, setCausal] = useState<CausalNetwork | null>(null);
  const [chartOrder, setChartOrder] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [qaLoading, setQaLoading] = useState(false);
  const [qaData, setQaData] = useState<QAResponse | null>(null);
  const [isRefining, setIsRefining] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [isSharing, setIsSharing] = useState(false);
  const [copied, setCopied] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const loadDashboard = useCallback(async (skipQA = false) => {
    setLoading(true);
    setError(null);

    // 1. Initial QA Gate Check
    if (!skipQA) {
      try {
        setQaLoading(true);
        const qaResult = await checkDataQuality(fileId);
        setQaData(qaResult);
        setQaLoading(false);

        // If it requires refinement, we stop here and let the user decide
        if (qaResult.requires_refinement) {
          setLoading(false);
          return;
        }
      } catch (err: any) {
        console.warn("QA check failed, proceeding to dashboard directly", err);
        setQaLoading(false);
      }
    }

    // 2. Load Dashboard (Standard Flow)

    const MAX_RETRIES = 2;
    let lastErr: any = null;

    for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
      try {
        if (attempt > 0) {
          console.log(`[DashboardPanel] Retry attempt ${attempt}/${MAX_RETRIES}...`);
          await new Promise(r => setTimeout(r, 1500 * attempt));
        }
        const data = await getDashboard(fileId, locale);
        if (!data || typeof data !== "object") {
          throw new Error("Invalid dashboard response");
        }
        setDashboard(data);
        const charts = Array.isArray(data.charts) ? data.charts : [];
        setChartOrder(charts.map((_, i) => `chart-${i}`));
        setLoading(false);
        return; // Success — exit
      } catch (err: any) {
        lastErr = err;
        const status = err?.response?.status;
        if (status === 500 && attempt < MAX_RETRIES) {
          console.warn(`[DashboardPanel] Got 500, retrying (${attempt + 1}/${MAX_RETRIES})...`);
          continue;
        }
        break; // Non-retryable error or max retries reached
      }
    }

    try {
      const causalData = await getCausalNetwork(fileId);
      if (!causalData.error && causalData.nodes.length > 0) {
        setCausal(causalData);
      }
    } catch (e) {
      console.warn("Causal network failed or unavailable", e);
    }

    console.error("[DashboardPanel] Error loading dashboard:", lastErr);
    const detail = lastErr?.response?.data?.detail || lastErr?.response?.data?.message || lastErr?.message || "Failed to generate dashboard";
    setError(typeof detail === "string" ? detail : "Failed to generate dashboard");
    setLoading(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fileId]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      setChartOrder((items) => {
        const oldIndex = items.indexOf(active.id as string);
        const newIndex = items.indexOf(over.id as string);
        return arrayMove(items, oldIndex, newIndex);
      });
    }
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
      <div className="glass-card p-8 text-center space-y-4">
        <p className="text-red-400">{error}</p>
        <button
          onClick={() => loadDashboard(true)}
          className="px-5 py-2.5 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-all font-semibold text-sm"
        >
          {t("retry") || "Retry"}
        </button>
      </div>
    );
  }

  const handleRefine = async () => {
    try {
      setIsRefining(true);
      await refineDataset(fileId);
      // Once refined, immediately load dashboard bypassing QA
      await loadDashboard(true);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to auto-refine data");
    } finally {
      setIsRefining(false);
    }
  };

  const handleShare = async () => {
    try {
      setIsSharing(true);
      const res = await createShare(fileId);
      setShareUrl(res.share_url);
    } catch (err) {
      console.error("Failed to create share link", err);
      alert("Failed to generate share link");
    } finally {
      setIsSharing(false);
    }
  };

  const copyToClipboard = () => {
    if (shareUrl) {
      navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // --- RENDERING QA BLOCK ---
  if (qaData?.requires_refinement && !dashboard) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] animate-in fade-in zoom-in duration-500">
        <div className="glass-card p-8 max-w-2xl w-full border-t-4 border-amber-500 shadow-2xl shadow-amber-500/10">
          <div className="flex items-center gap-4 mb-6">
            <div className="p-3 bg-amber-500/20 rounded-xl">
              <AlertTriangle className="w-8 h-8 text-amber-500" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">Data Quality Alert</h2>
              <p className="text-amber-400 font-mono text-sm mt-1">
                Health Score: {qaData.score}/100 • Rows: {qaData.row_count}
              </p>
            </div>
          </div>

          <div className="space-y-4 mb-8">
            <p className="text-slate-300 leading-relaxed">
              We intercepted your dataset before generating the dashboard because it contains severe structural and quality issues that mathematically compromise accurate forecasting.
            </p>
            <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-800">
              <h4 className="text-xs uppercase text-slate-500 font-bold mb-3">Detected Anomalies</h4>
              <ul className="space-y-2">
                {qaData.issues.map((issue, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-slate-300">
                    <span className="text-amber-500 mt-0.5">•</span>
                    {issue}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={handleRefine}
              disabled={isRefining}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white rounded-xl font-bold shadow-lg shadow-primary-500/20 transition-all hover:-translate-y-1 active:translate-y-0"
            >
              {isRefining ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  AI is Refining & Imputing Data...
                </>
              ) : (
                <>
                  ✨ Refine with AI Assistant
                </>
              )}
            </button>
            <button
              onClick={() => loadDashboard(true)}
              disabled={isRefining}
              className="px-6 py-4 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-300 rounded-xl font-semibold transition-colors"
            >
              Proceed with Raw Data
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!dashboard) return null;

  const charts = Array.isArray(dashboard.charts) ? dashboard.charts : [];
  const orderedCharts = chartOrder.map((id) => {
    const index = parseInt(id.replace("chart-", ""), 10);
    return charts[index];
  }).filter(Boolean);

  return (
    <div className="space-y-8">
      {/* Header with Auto-Detection Profile */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            {t("title")}
            {dashboard.detection_profile && (
              <span className="px-3 py-1 bg-primary-500/10 border border-primary-500/20 rounded-full text-[10px] font-bold text-primary-400 uppercase tracking-widest animate-pulse border-pulse">
                {dashboard.detection_profile}
              </span>
            )}
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            {t("insightsFor")} <span className="font-mono text-primary-400">{dashboard.file_id}</span>
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => window.open(`http://localhost:8000/api/export/${dashboard.file_id}/pdf`, "_blank")}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-all font-semibold border border-slate-700"
          >
            <Download className="w-4 h-4" />
            {t("export") || "PDF"}
          </button>
          <button
            onClick={handleShare}
            disabled={isSharing}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-lg transition-all font-semibold shadow-lg shadow-primary-500/20 disabled:opacity-50"
          >
            {isSharing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Share2 className="w-4 h-4" />}
            {t("share") || "Share"}
          </button>
        </div>
      </div>

      {/* Share Modal Overlay */}
      {shareUrl && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="glass-card max-w-md w-full p-6 shadow-2xl border-primary-500/30">
            <h3 className="text-xl font-bold mb-2">Share Dashboard</h3>
            <p className="text-sm text-slate-400 mb-6">Anyone with this link can view the analyzed dashboard and AI insights.</p>

            <div className="flex items-center gap-2 p-3 bg-slate-900 rounded-lg border border-slate-700 mb-6">
              <input
                readOnly
                value={shareUrl}
                className="flex-1 bg-transparent border-none text-sm text-slate-300 focus:outline-none"
              />
              <button
                onClick={copyToClipboard}
                className="p-2 hover:bg-slate-800 rounded-md transition-colors text-primary-400"
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>

            <button
              onClick={() => setShareUrl(null)}
              className="w-full py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl font-semibold transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Financial Health Section */}
      {dashboard.profit_loss && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-primary-400" />
            {t("financialSummary")}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="glass-card p-4 border-l-4 border-primary-500">
              <p className="text-xs text-slate-500">{t("totalRevenue")}</p>
              <p className="text-2xl font-bold mt-1">${(dashboard.profit_loss.total_revenue || 0).toLocaleString()}</p>
            </div>
            <div className="glass-card p-4 border-l-4 border-slate-600">
              <p className="text-xs text-slate-500">{t("totalCost")}</p>
              <p className="text-2xl font-bold mt-1 text-slate-300">${(dashboard.profit_loss.total_cost || 0).toLocaleString()}</p>
            </div>
            <div className={`glass-card p-4 border-l-4 ${dashboard.profit_loss.net_profit >= 0 ? 'border-emerald-500' : 'border-red-500'}`}>
              <div className="flex items-center justify-between">
                <p className="text-xs text-slate-500">{t("netProfit")}</p>
                {dashboard.profit_loss.net_profit >= 0 ? <TrendingUp className="w-4 h-4 text-emerald-500" /> : <TrendingDown className="w-4 h-4 text-red-500" />}
              </div>
              <p className={`text-2xl font-bold mt-1 ${dashboard.profit_loss.net_profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                ${(dashboard.profit_loss.net_profit || 0).toLocaleString()}
              </p>
            </div>
            <div className="glass-card p-4 border-l-4 border-violet-500">
              <p className="text-xs text-slate-500">{t("profitMargin")}</p>
              <p className="text-2xl font-bold mt-1 text-violet-400">{dashboard.profit_loss.margin_percentage}%</p>
            </div>
          </div>
        </div>
      )}

      {/* Summary stats (if no P&L) */}
      {!dashboard.profit_loss && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(dashboard.summary_stats).map(([key, val]) => (
            <div key={key} className="glass-card p-4">
              <p className="text-xs text-slate-500 capitalize">{key.replace(/_/g, " ")}</p>
              <p className="text-xl font-bold mt-1">
                {Array.isArray(val) ? val.length : String(val)}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Advanced Data Science & Health Section */}
      <div className="grid md:grid-cols-3 gap-6">
        {/* Data Quality Health Check */}
        {dashboard.data_quality && (
          <div className="glass-card p-6 border-t-2 border-emerald-500/50 flex flex-col h-full">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <h3 className="font-semibold text-slate-200">{t("dataHealth")}</h3>
              </div>
              <span className={`text-xl font-bold ${dashboard.data_quality.score > 80 ? 'text-emerald-400' : 'text-amber-400'}`}>
                {dashboard.data_quality.score}/100
              </span>
            </div>

            <div className="w-full h-2 bg-slate-800 rounded-full mb-6 overflow-hidden">
              <div
                className={`h-full transition-all duration-1000 ${dashboard.data_quality.score > 80 ? 'bg-emerald-500' : 'bg-amber-500'}`}
                style={{ width: `${dashboard.data_quality.score}%` }}
              />
            </div>

            <div className="space-y-4 flex-1">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                  <p className="text-[10px] uppercase text-slate-500 font-bold mb-1">{t("missing")}</p>
                  <p className="text-sm font-semibold">{dashboard.data_quality.missing_values_count}</p>
                </div>
                <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                  <p className="text-[10px] uppercase text-slate-500 font-bold mb-1">{t("duplicates")}</p>
                  <p className="text-sm font-semibold">{dashboard.data_quality.duplicates_count}</p>
                </div>
              </div>

              {dashboard.data_quality.issues.length > 0 && (
                <div className="space-y-2">
                  <p className="text-[10px] uppercase text-slate-500 font-bold">{t("cleanAlerts")}</p>
                  {dashboard.data_quality.issues.map((issue, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs text-amber-300/80 bg-amber-500/5 p-2 rounded border border-amber-500/10">
                      <Zap className="w-3 h-3" />
                      {issue}
                    </div>
                  ))}
                </div>
              )}
              {dashboard.data_quality.issues.length === 0 && (
                <div className="flex items-center gap-2 text-xs text-emerald-400/80 bg-emerald-500/5 p-3 rounded border border-emerald-500/10">
                  <CheckCircle2 className="w-4 h-4" />
                  {t("cleanState")}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Feature Importance (Predictive Power) */}
        {dashboard.feature_importance && (
          <div className="md:col-span-2 glass-card p-6 border-t-2 border-primary-500/50">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <Target className="w-5 h-5 text-primary-400" />
                <h3 className="font-semibold text-slate-200">{t("featureImportance")}</h3>
              </div>
              <div className="text-[10px] text-slate-500 font-mono">MODEL: RANDOM FOREST</div>
            </div>

            <div className="h-[200px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dashboard.feature_importance} layout="vertical" margin={{ left: 20, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                  <XAxis type="number" hide />
                  <YAxis
                    dataKey="feature_name"
                    type="category"
                    stroke="#94a3b8"
                    fontSize={10}
                    width={80}
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="glass-card p-3 border-slate-700 bg-slate-900/95 shadow-xl">
                            <p className="text-xs font-bold text-white mb-1">{data.feature_name}</p>
                            <div className="space-y-1">
                              <p className="text-[10px] text-slate-400">
                                Importance: <span className="text-primary-400 font-mono">{(data.importance_score * 100).toFixed(1)}%</span>
                              </p>
                              <p className="text-[10px] text-slate-400">
                                Impact: <span className={data.impact_level === 'High' ? 'text-primary-400' : 'text-slate-400'}>{data.impact_level}</span>
                              </p>
                              <div className="flex items-center gap-1 mt-2 pt-2 border-t border-slate-700/50">
                                {data.contribution_type === 'Positive' ? (
                                  <TrendingUp className="w-3 h-3 text-green-400" />
                                ) : data.contribution_type === 'Negative' ? (
                                  <TrendingDown className="w-3 h-3 text-red-400" />
                                ) : (
                                  <div className="w-3 h-0.5 bg-slate-500" />
                                )}
                                <span className={`text-[10px] font-bold ${data.contribution_type === 'Positive' ? 'text-green-400' : data.contribution_type === 'Negative' ? 'text-red-400' : 'text-slate-500'}`}>
                                  {data.contribution_type} Contribution
                                </span>
                              </div>
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar dataKey="importance_score" radius={[0, 4, 4, 0]}>
                    {dashboard.feature_importance.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.impact_level === 'High' ? '#3b82f6' : entry.impact_level === 'Medium' ? '#6366f1' : '#94a3b8'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="text-[11px] text-slate-500 mt-4 text-center">
              This model identifies which variables most accurately predict your primary business targets.
            </p>
          </div>
        )}
      </div>

      {/* Causal Inference Network */}
      {causal && causal.nodes && causal.links && causal.nodes.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Target className="w-5 h-5 text-indigo-400" />
              Causal Inference (DAG)
            </h2>
            <div className="text-[10px] text-slate-500 font-mono">MODEL: PARTIAL CORRELATION (PINGOUIN)</div>
          </div>
          <div className="glass-card p-6 border-t-2 border-indigo-500/50 relative overflow-hidden h-[500px]">
            <ForceGraph2D
              graphData={causal}
              width={800}
              height={450}
              nodeAutoColorBy="group"
              nodeLabel="id"
              linkDirectionalArrowLength={3.5}
              linkDirectionalArrowRelPos={1}
              linkColor={(link: any) => link.value > 0 ? '#10b981' : '#f43f5e'}
              linkWidth={(link: any) => Math.max(1, Math.abs(link.value * 5))}
              nodeCanvasObject={(node: any, ctx, globalScale) => {
                const label = node.id;
                const fontSize = 12 / globalScale;
                ctx.font = `${fontSize}px Sans-Serif`;
                const textWidth = ctx.measureText(label).width;
                const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);

                ctx.fillStyle = 'rgba(30, 41, 59, 0.8)';
                ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, bckgDimensions[0], bckgDimensions[1]);

                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = node.color;
                ctx.fillText(label, node.x, node.y);

                node.__bckgDimensions = bckgDimensions;
              }}
            />
          </div>
        </div>
      )}

      {/* Legacy Data Science Section */}
      {(dashboard.correlations || dashboard.anomalies) && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Zap className="w-5 h-5 text-indigo-400" />
            {t("statsAnomalies")}
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            {/* Key Drivers (Correlations) */}
            {dashboard.correlations && (
              <div className="glass-card p-6 border-t-2 border-indigo-500/50">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-indigo-400" />
                    <h3 className="font-semibold text-slate-200">{t("keyDrivers")}</h3>
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono">MODEL: PEARSON CORRELATION</div>
                </div>
                <div className="space-y-3">
                  {dashboard.correlations.map((c, i) => (
                    <div key={i} className="flex items-center justify-between p-3 bg-indigo-500/5 rounded-lg border border-indigo-500/10 group hover:bg-indigo-500/10 transition-colors">
                      <div className="min-w-0">
                        <p className="text-xs font-semibold text-slate-300 truncate">
                          {c.column_a} <span className="text-indigo-500 mx-1">&</span> {c.column_b}
                        </p>
                        <p className="text-[10px] text-slate-500">{c.description}</p>
                      </div>
                      <div className="text-right ml-4">
                        <span className={`text-sm font-bold ${Math.abs(c.correlation) > 0.8 ? 'text-indigo-400' : 'text-slate-400'}`}>
                          {c.correlation > 0 ? '+' : ''}{(c.correlation * 100).toFixed(0)}%
                        </span>
                        <div className="w-12 h-1 bg-slate-800 rounded-full mt-1 overflow-hidden">
                          <div
                            className="h-full bg-indigo-500"
                            style={{ width: `${Math.abs(c.correlation) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Anomaly Alerts */}
            {dashboard.anomalies && (
              <div className="glass-card p-6 border-t-2 border-rose-500/50">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-rose-400" />
                    <h3 className="font-semibold text-slate-200">{t("anomalyAlerts")}</h3>
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono">MODEL: ISOLATION FOREST</div>
                </div>
                <div className="space-y-3">
                  {dashboard.anomalies.map((a, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-rose-500/5 rounded-lg border border-rose-500/10">
                      <div className="p-1 bg-rose-500/20 rounded mt-0.5">
                        <Zap className="w-3 h-3 text-rose-400" />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-xs font-bold text-slate-300 uppercase letter-spacing-wide">{a.column}</p>
                          <span className="text-[10px] text-slate-500">Row {a.row_index}</span>
                        </div>
                        <p className="text-xs text-rose-300/80 mt-0.5">{a.reason}</p>
                        <p className="text-xs font-mono text-slate-400 mt-1">Value: {(a.value || 0).toLocaleString()}</p>
                      </div>
                    </div>
                  ))}
                  {dashboard.anomalies.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-8 text-slate-600">
                      <ShieldCheck className="w-8 h-8 mb-2 opacity-20" />
                      <p className="text-xs">{t("noAnomalies")}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Large Scale Classification & Segmentation */}
      {dashboard.segments && dashboard.segments.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Target className="w-5 h-5 text-emerald-400" />
              {t("marketClass")}
            </h2>
            <div className="text-[10px] text-slate-500 font-mono">MODEL: HDBSCAN CLUSTERING</div>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {/* Segment Composition */}
            <div className="md:col-span-1 glass-card p-6 border-t-2 border-emerald-500/50">
              <h3 className="text-sm font-semibold mb-6 flex items-center gap-2">
                <PieChart className="w-4 h-4 text-emerald-400" />
                {t("clusterComp")}
              </h3>
              <div className="h-[240px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={dashboard.segments}
                      nameKey="name"
                      dataKey="size"
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                    >
                      {dashboard.segments.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px" }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4 space-y-2">
                {dashboard.segments.map((s, i) => (
                  <div key={i} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                      <span className="text-slate-300 truncate w-32">{s.name}</span>
                    </div>
                    <span className="text-slate-500 font-mono">{s.size} records</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Segment Strategies */}
            <div className="md:col-span-2 glass-card p-6 border-t-2 border-primary-500/50 overflow-hidden">
              <h3 className="text-sm font-semibold mb-6 flex items-center gap-2">
                <Lightbulb className="w-4 h-4 text-primary-400" />
                {t("segmentStrategies")}
              </h3>
              <div className="space-y-6 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                {dashboard.segments.map((s, i) => (
                  <div key={i} className="p-4 bg-slate-800/40 rounded-xl border border-slate-700/50 group hover:border-primary-500/30 transition-colors">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-bold text-primary-300">{s.name}</h4>
                      <div className="px-2 py-0.5 bg-primary-500/10 rounded text-[10px] font-bold text-primary-400 uppercase">
                        {s.name.toUpperCase().startsWith("SEGMENT") ? s.name : `Cluster ${i + 1}`}
                      </div>
                    </div>
                    <p className="text-xs text-slate-400 mb-3 italic">"{s.characteristics}"</p>
                    <div className="pl-3 border-l-2 border-primary-500/20">
                      <p className="text-xs font-semibold text-slate-300 mb-1">{t("growthPlanLabel")}</p>
                      <p className="text-xs text-slate-400 leading-relaxed">{s.growth_strategy}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Business Growth Plan */}
      {dashboard.growth_suggestions && dashboard.growth_suggestions.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-amber-400" />
              {t("growthPlan")}
            </h2>
            <div className="px-3 py-1 bg-amber-500/10 rounded-full border border-amber-500/20">
              <span className="text-[10px] font-bold text-amber-500 uppercase tracking-wider">AI Generated</span>
            </div>
          </div>
          <div className="grid md:grid-cols-3 gap-4">
            {dashboard.growth_suggestions.map((s, i) => (
              <div key={i} className="glass-card p-5 relative overflow-hidden group hover:border-primary-500/50 transition-colors">
                <div className="relative z-10">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-bold text-slate-100 group-hover:text-primary-300 transition-colors">{s.title}</h3>
                    <Target className="w-4 h-4 text-slate-600 group-hover:text-primary-500/50" />
                  </div>
                  <p className="text-sm text-slate-400 leading-relaxed mb-4">{s.description}</p>
                  <div className="flex gap-4">
                    <div>
                      <p className="text-[10px] uppercase text-slate-500 font-semibold mb-1">Impact</p>
                      <span className={`text-xs px-2 py-0.5 rounded ${s.impact === 'High' ? 'bg-emerald-500/10 text-emerald-500' :
                        s.impact === 'Medium' ? 'bg-amber-500/10 text-amber-500' : 'bg-slate-500/10 text-slate-500'
                        }`}>
                        {s.impact}
                      </span>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase text-slate-500 font-semibold mb-1">Feasibility</p>
                      <span className={`text-xs px-2 py-0.5 rounded ${s.feasibility === 'High' ? 'bg-emerald-500/10 text-emerald-500' :
                        s.feasibility === 'Medium' ? 'bg-amber-500/10 text-amber-500' : 'bg-slate-500/10 text-slate-500'
                        }`}>
                        {s.feasibility}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Time Series Decomposition */}
      {dashboard.time_series_decomposition && (
        <TimeDecompositionChart decomposition={dashboard.time_series_decomposition} />
      )}

      {/* Draggable Charts */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <ArrowUpRight className="w-5 h-5 text-primary-400" />
          {t("visuals")}
        </h2>
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={chartOrder} strategy={rectSortingStrategy}>
            <div className="grid md:grid-cols-2 gap-6">
              {orderedCharts.map((chart, i) => (
                <SortableChartCard key={chartOrder[i]} id={chartOrder[i]} chart={chart} />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      </div>
    </div>
  );
}
