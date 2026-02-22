"use client";

import { User, Mail, ShieldCheck, ExternalLink, X } from "lucide-react";
import { useTranslations } from "next-intl";

interface Props {
    onClose: () => void;
}

export default function DeveloperProfile({ onClose }: Props) {
    const t = useTranslations("Profile");

    return (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-[60] p-4 backdrop-blur-sm">
            <div className="glass-card p-8 w-full max-w-lg relative overflow-hidden group">
                {/* Animated Background Glow */}
                <div className="absolute -top-24 -right-24 w-48 h-48 bg-primary-500/10 blur-[100px] group-hover:bg-primary-500/20 transition-colors duration-500" />

                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 p-2 hover:bg-slate-800 rounded-full transition-colors z-10"
                >
                    <X className="w-5 h-5 text-slate-400" />
                </button>

                <div className="relative z-10">
                    <div className="flex flex-col items-center text-center">
                        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center mb-6 shadow-xl shadow-primary-500/20">
                            <User className="w-10 h-10 text-white" />
                        </div>

                        <h2 className="text-2xl font-bold text-white mb-1">MR. KYAW ZIN TUN</h2>
                        <div className="flex items-center gap-2 text-primary-400 font-medium text-sm mb-6">
                            <ShieldCheck className="w-4 h-4" />
                            {t("role")}
                        </div>

                        <p className="text-slate-400 text-sm leading-relaxed mb-8 max-w-sm">
                            {t("desc")}
                        </p>

                        <div className="w-full space-y-3">
                            <a
                                href="mailto:itsolutions.mm@gmail.com"
                                className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl border border-slate-700/50 hover:border-primary-500/50 hover:bg-slate-800 transition-all group/link"
                            >
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-slate-700 rounded-lg group-hover/link:bg-primary-500/20 group-hover/link:text-primary-400 transition-colors">
                                        <Mail className="w-4 h-4" />
                                    </div>
                                    <span className="text-sm font-medium text-slate-200">itsolutions.mm@gmail.com</span>
                                </div>
                                <ExternalLink className="w-4 h-4 text-slate-500 group-hover/link:text-primary-400" />
                            </a>

                            <div className="p-4 bg-primary-500/5 rounded-xl border border-primary-500/10 text-center">
                                <p className="text-[10px] uppercase tracking-widest text-primary-400/60 font-bold mb-1">{t("statusLabel")}</p>
                                <div className="flex items-center justify-center gap-1.5">
                                    <span className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
                                    <span className="text-xs font-semibold text-slate-300">{t("statusValue")}</span>
                                </div>
                            </div>
                        </div>

                        <p className="mt-8 text-[11px] text-slate-600 font-medium">
                            {t("footer")}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
