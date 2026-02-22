"use client";

import { useState, useEffect } from "react";
import { X, Key, Check, Trash2, Loader2 } from "lucide-react";
import { useTranslations } from "next-intl";
import { getApiKeyStatus, setApiKey, removeApiKey, type ApiKeyStatus } from "@/lib/api";

interface Props {
  onClose: () => void;
}

export default function SettingsModal({ onClose }: Props) {
  const t = useTranslations("Settings");
  const [keyStatus, setKeyStatus] = useState<ApiKeyStatus | null>(null);
  const [newKey, setNewKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    getApiKeyStatus().then(setKeyStatus).catch(() => { });
  }, []);

  const handleSaveKey = async () => {
    if (!newKey.trim()) return;
    setSaving(true);
    try {
      const status = await setApiKey(newKey.trim());
      setKeyStatus(status);
      setNewKey("");
      setMessage(t("saveSuccess"));
      setTimeout(() => setMessage(null), 3000);
    } catch {
      setMessage(t("saveFailed"));
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveKey = async () => {
    await removeApiKey();
    const status = await getApiKeyStatus();
    setKeyStatus(status);
    setMessage(t("removeSuccess"));
    setTimeout(() => setMessage(null), 3000);
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="glass-card p-6 w-full max-w-md">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold">{t("title")}</h2>
          <button onClick={onClose} className="p-2 hover:bg-slate-700 rounded-lg transition">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* API Key Section */}
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-medium flex items-center gap-2 mb-3">
              <Key className="w-4 h-4 text-primary-500" />
              {t("apiKeyTitle")}
            </h3>
            <p className="text-xs text-slate-500 mb-3">
              {t("apiKeyDesc")}
            </p>

            {keyStatus && (
              <div className="flex items-center gap-2 mb-3 bg-slate-800 rounded-lg p-3">
                <span className="text-xs text-slate-400">{t("current")}</span>
                <code className="text-xs text-primary-300 flex-1">
                  {keyStatus.has_key ? keyStatus.key_preview : t("noKey")}
                </code>
                {keyStatus.has_key && (
                  <button onClick={handleRemoveKey} className="p-1 hover:bg-red-500/10 rounded" title={t("removeKey")}>
                    <Trash2 className="w-3.5 h-3.5 text-red-400" />
                  </button>
                )}
              </div>
            )}

            <div className="flex gap-2">
              <input
                type="password"
                value={newKey}
                onChange={(e) => setNewKey(e.target.value)}
                placeholder="sk-..."
                className="flex-1 bg-slate-800 rounded-lg px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 outline-none focus:ring-2 focus:ring-primary-500/50"
              />
              <button
                onClick={handleSaveKey}
                disabled={!newKey.trim() || saving}
                className="px-4 py-2.5 bg-primary-600 hover:bg-primary-700 disabled:opacity-40 rounded-lg transition"
              >
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {message && (
            <div className="text-sm text-center text-green-400 bg-green-500/10 rounded-lg py-2">
              {message}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
