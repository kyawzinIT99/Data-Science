"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, Loader2 } from "lucide-react";
import { uploadFile, uploadMultiFile, type FileUploadResponse } from "@/lib/api";

interface Props {
  onUpload: (file: FileUploadResponse) => void;
}

export default function FileUploader({ onUpload }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;
      setLoading(true);
      setError(null);
      try {
        let result;
        if (acceptedFiles.length === 1) {
          result = await uploadFile(acceptedFiles[0]);
        } else {
          result = await uploadMultiFile(acceptedFiles);
        }
        onUpload(result);
      } catch (err: any) {
        setError(err.response?.data?.detail || "Upload failed. Please try again.");
      } finally {
        setLoading(false);
      }
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
      "application/json": [".json"],
    },
  });

  return (
    <div className="w-full max-w-2xl">
      <div
        {...getRootProps()}
        className={`gradient-border p-12 text-center cursor-pointer transition-all hover:scale-[1.01] ${isDragActive ? "pulse-glow" : ""
          } ${loading ? "opacity-60 pointer-events-none" : ""}`}
      >
        <input {...getInputProps()} />

        {loading ? (
          <div className="space-y-4">
            <Loader2 className="w-12 h-12 text-primary-500 animate-spin mx-auto" />
            <p className="text-slate-300">Processing your file with AI...</p>
            <p className="text-xs text-slate-500">Extracting text, chunking, and creating embeddings</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-primary-600/20 flex items-center justify-center mx-auto">
              {isDragActive ? (
                <FileText className="w-8 h-8 text-primary-400" />
              ) : (
                <Upload className="w-8 h-8 text-primary-400" />
              )}
            </div>
            <div>
              <p className="text-lg font-medium text-slate-200">
                {isDragActive ? "Drop your files here" : "Drag & drop your files here (can select multiple)"}
              </p>
              <p className="text-sm text-slate-500 mt-1">or click to browse</p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center">
              {["CSV", "Excel", "PDF", "Word", "TXT", "JSON"].map((type) => (
                <span
                  key={type}
                  className="px-3 py-1 text-xs rounded-full bg-slate-800 text-slate-400"
                >
                  {type}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}
    </div>
  );
}
