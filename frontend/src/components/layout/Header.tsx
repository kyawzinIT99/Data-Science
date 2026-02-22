"use client";

import { useState, useRef, useEffect } from "react";
import { Brain, Sun, Moon, Settings, User, Languages, ChevronDown, ArrowLeft } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { useTheme } from "@/lib/theme";
import SettingsModal from "@/components/ui/SettingsModal";
import DeveloperProfile from "@/components/ui/DeveloperProfile";
import { useRouter, usePathname, locales, localeNames } from "@/navigation";

export default function Header() {
  const { theme, toggleTheme } = useTheme();
  const t = useTranslations("Header");
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();

  const menuRef = useRef<HTMLDivElement>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [showLangMenu, setShowLangMenu] = useState(false);

  const searchParams = useSearchParams();
  const fileId = searchParams.get("fileId");

  const handleBackToLibrary = () => {
    const params = new URLSearchParams(searchParams.toString());
    params.delete("fileId");
    const newQuery = params.toString();
    router.replace(pathname + (newQuery ? `?${newQuery}` : ""));
  };

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowLangMenu(false);
      }
    }
    if (showLangMenu) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showLangMenu]);

  const handleLanguageChange = (newLocale: string) => {
    router.replace(pathname, { locale: newLocale });
    setShowLangMenu(false);
  };

  return (
    <>
      <header className="border-b border-slate-800 bg-dark-950/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-primary-600/20">
              <Brain className="w-6 h-6 text-primary-500 relative z-10" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                {t("title")}
              </h1>
              <p className="text-xs text-slate-500">{t("subtitle")}</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {fileId && (
              <button
                onClick={handleBackToLibrary}
                className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-slate-300 hover:text-primary-400 hover:bg-slate-800 rounded-xl transition group"
              >
                <ArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-1" />
                <span className="hidden md:inline">Back to Library</span>
              </button>
            )}

            <div className="flex items-center gap-2">
              {/* Language Switcher */}
              <div className="relative mr-2" ref={menuRef}>
                <button
                  onClick={() => setShowLangMenu(!showLangMenu)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-xl transition text-sm font-medium ${showLangMenu ? 'bg-primary-500/10 text-primary-400 ring-2 ring-primary-500/20' : 'bg-slate-800 hover:bg-slate-700 text-slate-300'}`}
                >
                  <Languages className="w-4 h-4 text-primary-400" />
                  <span className="hidden sm:inline">{localeNames[locale]}</span>
                  <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${showLangMenu ? 'rotate-180' : ''}`} />
                </button>

                {showLangMenu && (
                  <div className="absolute right-0 mt-2 w-48 bg-slate-800 border border-slate-700 rounded-xl shadow-2xl overflow-hidden z-[60] max-h-[60vh] overflow-y-auto animate-in fade-in zoom-in-95 duration-200 origin-top-right">
                    <div className="py-1">
                      {locales.map((l) => (
                        <button
                          key={l}
                          onClick={() => handleLanguageChange(l)}
                          className={`w-full text-left px-4 py-3 text-sm transition-colors flex items-center justify-between group ${locale === l ? 'text-primary-400 bg-primary-400/5 font-semibold' : 'text-slate-300 hover:bg-slate-700'
                            }`}
                        >
                          <span>{localeNames[l]}</span>
                          {locale === l && <div className="w-1.5 h-1.5 rounded-full bg-primary-500 shadow-[0_0_8px_rgba(59,130,246,0.6)]" />}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <button
                onClick={() => setShowProfile(true)}
                className="p-2.5 hover:bg-slate-800 rounded-xl transition text-slate-400 hover:text-primary-400"
                title={t("profile")}
              >
                <User className="w-5 h-5" />
              </button>
              <button
                onClick={toggleTheme}
                className="p-2.5 hover:bg-slate-800 rounded-xl transition"
                title={theme === "dark" ? t("themeLight") : t("themeDark")}
              >
                {theme === "dark" ? (
                  <Sun className="w-5 h-5 text-slate-400" />
                ) : (
                  <Moon className="w-5 h-5 text-slate-400" />
                )}
              </button>
              <button
                onClick={() => setShowSettings(true)}
                className="p-2.5 hover:bg-slate-800 rounded-xl transition"
                title={t("settings")}
              >
                <Settings className="w-5 h-5 text-slate-400" />
              </button>
            </div>
          </div>
        </div>
      </header>
      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
      {showProfile && <DeveloperProfile onClose={() => setShowProfile(false)} />}

    </>
  );
}
