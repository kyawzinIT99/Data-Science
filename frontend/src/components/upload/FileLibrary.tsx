"use client";

import { useState, useEffect } from "react";
import { FileText, Trash2, Clock, HardDrive, Loader2 } from "lucide-react";
import { listFiles, deleteFile, type FileRecord, type FileUploadResponse } from "@/lib/api";

interface Props {
  onSelectFile: (file: FileUploadResponse) => void;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

export default function FileLibrary({ onSelectFile }: Props) {
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listFiles()
      .then(setFiles)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (fileId: string) => {
    await deleteFile(fileId);
    setFiles((prev) => prev.filter((f) => f.file_id !== fileId));
  };

  const handleSelect = (f: FileRecord) => {
    onSelectFile({
      file_id: f.file_id,
      filename: f.filename,
      file_type: f.file_type,
      num_chunks: f.num_chunks,
      preview: "",
    });
  };

  if (loading) {
    return (
      <div className="text-center py-6">
        <Loader2 className="w-5 h-5 animate-spin mx-auto text-slate-500" />
      </div>
    );
  }

  if (files.length === 0) return null;

  return (
    <div className="w-full max-w-2xl mt-8">
      <h3 className="text-sm font-medium text-slate-400 mb-3">Recent Files</h3>
      <div className="space-y-2">
        {files.slice(0, 10).map((f) => (
          <div
            key={f.file_id}
            className="glass-card p-3 flex items-center justify-between hover:bg-slate-800/60 transition cursor-pointer group"
            onClick={() => handleSelect(f)}
          >
            <div className="flex items-center gap-3">
              <FileText className="w-5 h-5 text-primary-400" />
              <div>
                <p className="text-sm font-medium">{f.filename}</p>
                <div className="flex gap-3 text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatDate(f.uploaded_at)}
                  </span>
                  <span className="flex items-center gap-1">
                    <HardDrive className="w-3 h-3" />
                    {formatSize(f.file_size)}
                  </span>
                  <span>{f.num_chunks} chunks</span>
                </div>
              </div>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); handleDelete(f.file_id); }}
              className="p-2 hover:bg-red-500/10 rounded-lg transition opacity-0 group-hover:opacity-100"
            >
              <Trash2 className="w-4 h-4 text-red-400" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
