import { createNavigation } from 'next-intl/navigation';
import { defineRouting } from 'next-intl/routing';

export const locales = ['en', 'th', 'fr', 'my'] as const;
export const localeNames: Record<string, string> = {
    en: "English",
    th: "ไทย",
    fr: "Français",
    my: "မြန်မာ"
};

export const routing = defineRouting({
    locales,
    defaultLocale: 'en'
});

export const { Link, redirect, usePathname, useRouter } = createNavigation(routing);
