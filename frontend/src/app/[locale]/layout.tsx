import type { Metadata } from "next";
import "@/styles/globals.css";
import { ThemeProvider } from "@/lib/theme";
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import dynamic from "next/dynamic";

const ParticleBackground = dynamic(() => import("@/components/ui/ParticleBackground"), {
  ssr: false
});

import { locales } from "@/navigation";
import { setRequestLocale } from 'next-intl/server';

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export const metadata: Metadata = {
  title: "AI Data Analysis Platform",
  description: "Upload and analyze your documents with AI",
};

import LoginWall from "@/components/auth/LoginWall";

export default async function RootLayout({
  children,
  params: { locale }
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  // Enable static rendering
  setRequestLocale(locale);
  const messages = await getMessages({ locale });

  return (
    <html lang={locale} suppressHydrationWarning>
      {/* We removed bg-dark-900 here because the ParticleBackground needs to be visible behind content, and elements often stack on Top of Body */}
      <body className="min-h-screen text-slate-100 antialiased bg-slate-900 relative">
        <NextIntlClientProvider messages={messages}>
          <ThemeProvider>
            <ParticleBackground />
            <LoginWall>
              {children}
            </LoginWall>
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
