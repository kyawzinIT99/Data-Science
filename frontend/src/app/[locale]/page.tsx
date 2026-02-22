"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { Download, FileJson, Loader2, Share2, Mail, ArrowLeft } from "lucide-react";
import { useTranslations } from "next-intl";
import { Suspense } from "react";
import FileUploader from "@/components/upload/FileUploader";
import FileLibrary from "@/components/upload/FileLibrary";
import dynamic from "next/dynamic";

const AnalysisPanel = dynamic(() => import("@/components/dashboard/AnalysisPanel"), {
  loading: () => <div className="flex justify-center p-12"><Loader2 className="w-8 h-8 animate-spin text-primary-500" /></div>
});
const ChatPanel = dynamic(() => import("@/components/chat/ChatPanel"), {
  loading: () => <div className="flex justify-center p-12"><Loader2 className="w-8 h-8 animate-spin text-primary-500" /></div>
});
const DashboardPanel = dynamic(() => import("@/components/dashboard/DashboardPanel"), {
  ssr: false, // Force Graph cannot be SSR'd
  loading: () => <div className="flex justify-center p-12"><Loader2 className="w-8 h-8 animate-spin text-primary-500" /></div>
});
const CleaningPanel = dynamic(() => import("@/components/dashboard/CleaningPanel"), {
  loading: () => <div className="flex justify-center p-12"><Loader2 className="w-8 h-8 animate-spin text-primary-500" /></div>
});
const ComparePanel = dynamic(() => import("@/components/dashboard/ComparePanel"), {
  loading: () => <div className="flex justify-center p-12"><Loader2 className="w-8 h-8 animate-spin text-primary-500" /></div>
});
import ShareModal from "@/components/ui/ShareModal";
import EmailModal from "@/components/ui/EmailModal";
import Header from "@/components/layout/Header";
import { useRouter, usePathname } from "@/navigation";
import { exportPdfReport, exportJsonReport, type FileUploadResponse } from "@/lib/api";

type Tab = "analysis" | "chat" | "dashboard" | "cleaning" | "compare";

function HomeContent() {
  const t = useTranslations("Home");
  const [uploadedFile, setUploadedFile] = useState<FileUploadResponse | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("analysis");
  const [exporting, setExporting] = useState<string | null>(null);
  const [showShare, setShowShare] = useState(false);
  const [showEmail, setShowEmail] = useState(false);

  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const fileIdFromUrl = searchParams.get("fileId");

  // Restore file from URL on mount or change
  useEffect(() => {
    if (!fileIdFromUrl) {
      setUploadedFile(null);
      return;
    }
    if (!uploadedFile || uploadedFile.file_id !== fileIdFromUrl) {
      import("@/lib/api").then(({ listFiles }) => {
        listFiles().then((files) => {
          const file = files.find(f => f.file_id === fileIdFromUrl);
          if (file) {
            setUploadedFile({
              file_id: file.file_id,
              filename: file.filename,
              file_type: file.file_type,
              num_chunks: file.num_chunks,
              preview: ""
            });
          }
        });
      });
    }
  }, [fileIdFromUrl, uploadedFile]);

  const handleSetFile = (file: FileUploadResponse | null) => {
    setUploadedFile(file);
    const params = new URLSearchParams(searchParams.toString());
    if (file) {
      params.set("fileId", file.file_id);
    } else {
      params.delete("fileId");
    }
    const newQuery = params.toString();
    router.replace(pathname + (newQuery ? `?${newQuery}` : ""));
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: "analysis", label: t("tabs.analysis") },
    { key: "chat", label: t("tabs.chat") },
    { key: "dashboard", label: t("tabs.dashboard") },
    { key: "cleaning", label: t("tabs.cleaning") },
    { key: "compare", label: t("tabs.compare") },
  ];

  const handleExport = async (format: "pdf" | "json") => {
    if (!uploadedFile || exporting) return;
    setExporting(format);
    try {
      if (format === "pdf") {
        await exportPdfReport(uploadedFile.file_id);
      } else {
        await exportJsonReport(uploadedFile.file_id);
      }
    } catch {
      alert(t("messages.exportFailed"));
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-8 relative z-10">
        {!uploadedFile ? (
          <div className="flex flex-col items-center justify-center min-h-[60vh]">
            <FileUploader onUpload={handleSetFile} />
            <FileLibrary onSelectFile={handleSetFile} />
          </div>
        ) : (
          <div className="space-y-6">
            {/* File info bar */}
            <div className="glass-card p-4 flex items-center justify-between flex-wrap gap-3">
              <div>
                <p className="text-sm text-slate-400">{t("fileInfo.label")}</p>
                <p className="font-semibold">{uploadedFile.filename}</p>
                <p className="text-xs text-slate-500">
                  {uploadedFile.num_chunks} {t("fileInfo.chunks")}
                </p>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <button
                  onClick={() => handleExport("pdf")}
                  disabled={!!exporting}
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-primary-600 hover:bg-primary-700 disabled:opacity-50 rounded-lg transition"
                >
                  {exporting === "pdf" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                  {t("actions.exportPdf")}
                </button>
                <button
                  onClick={() => handleExport("json")}
                  disabled={!!exporting}
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-slate-700 hover:bg-slate-600 disabled:opacity-50 rounded-lg transition"
                >
                  {exporting === "json" ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileJson className="w-4 h-4" />}
                  {t("actions.json")}
                </button>
                <button
                  onClick={() => setShowShare(true)}
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-slate-700 hover:bg-slate-600 rounded-lg transition"
                >
                  <Share2 className="w-4 h-4" />
                  {t("actions.share")}
                </button>
                <button
                  onClick={() => setShowEmail(true)}
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-slate-700 hover:bg-slate-600 rounded-lg transition"
                >
                  <Mail className="w-4 h-4" />
                  {t("actions.email")}
                </button>
                <div className="flex items-center gap-3 px-4 py-2 bg-slate-800/50 rounded-lg border border-slate-700">
                  <div className="p-1 px-2 bg-primary-500/10 text-primary-400 text-xs font-mono rounded border border-primary-500/20 shadow-[0_0_10px_rgba(59,130,246,0.1)]">
                    File ID: {uploadedFile.file_id}
                  </div>
                  <span className="text-slate-400">|</span>
                  <div className="flex items-center gap-2 text-slate-300 text-sm">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                    {uploadedFile.num_chunks} {t("fileInfo.chunks")}
                  </div>
                </div>
              </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 overflow-x-auto pb-1">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`px-5 py-2.5 rounded-lg text-sm font-medium transition whitespace-nowrap ${activeTab === tab.key
                    ? "bg-primary-600 text-white"
                    : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                    }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div>
              {activeTab === "analysis" && <AnalysisPanel fileId={uploadedFile.file_id} />}
              {activeTab === "chat" && <ChatPanel fileId={uploadedFile.file_id} />}
              {activeTab === "dashboard" && <DashboardPanel fileId={uploadedFile.file_id} />}
              {activeTab === "cleaning" && <CleaningPanel fileId={uploadedFile.file_id} />}
              {activeTab === "compare" && <ComparePanel primaryFileId={uploadedFile.file_id} />}
            </div>
          </div>
        )}
      </main>

      {/* Share Modal */}
      {showShare && uploadedFile && (
        <ShareModal fileId={uploadedFile.file_id} onClose={() => setShowShare(false)} />
      )}

      {/* Email Modal */}
      {showEmail && uploadedFile && (
        <EmailModal fileId={uploadedFile.file_id} onClose={() => setShowEmail(false)} />
      )}
    </div>
  );
}

export default function Home() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    }>
      <HomeContent />
    </Suspense>
  );
}
