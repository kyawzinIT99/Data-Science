import { ReactNode } from 'react';
import "@/styles/globals.css";

export default function SharedLayout({ children }: { children: ReactNode }) {
    return (
        <html lang="en">
            <body className="bg-slate-900 text-slate-100 min-h-screen font-sans">
                {children}
            </body>
        </html>
    );
}
