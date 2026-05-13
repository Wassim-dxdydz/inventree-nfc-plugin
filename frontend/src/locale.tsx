import type { InvenTreePluginContext } from '@inventreedb/ui';
import { I18nProvider } from '@lingui/react';
import { useEffect, useState } from 'react';

// Vite resolves this glob at build time — every messages file in locales/
// is automatically included in the bundle. Adding a new language = zero code changes.
const catalogs = import.meta.glob('./locales/*/messages.ts', { eager: true });

function getCatalog(locale: string): any {
  // Try exact match first (handles zh_Hans, zh_Hant, pseudo-LOCALE etc.)
  const exact = catalogs[`./locales/${locale}/messages.ts`] as any;
  if (exact) return exact.default ?? exact.messages ?? exact;

  // Try base language (en-us → en, fr-CA → fr)
  const base = locale.split(/[-_]/)[0];
  const fallback = catalogs[`./locales/${base}/messages.ts`] as any;
  if (fallback) return fallback.default ?? fallback.messages ?? fallback;

  // Last resort: English
  const en = catalogs[`./locales/en/messages.ts`] as any;
  return en?.default ?? en?.messages ?? en ?? {};
}

let catalogLoaded = false;

export function LocalizedComponent({
  locale: _locale,
  children,
  context
}: {
  locale: string;
  children: React.ReactNode;
  context: InvenTreePluginContext;
}) {
  const [ready, setReady] = useState(catalogLoaded);

  useEffect(() => {
    if (catalogLoaded) return;

    const activeLocale = context.i18n.locale;
    const base = activeLocale.split(/[-_]/)[0];
    const catalog = getCatalog(activeLocale);

    context.i18n.load(base, {
      ...((context.i18n as any)._messages?.[base] ?? {}),
      ...catalog
    });
    context.i18n.activate(base);
    catalogLoaded = true;
    setReady(true);
  }, [context.i18n]);

  if (!ready) return null;

  return <I18nProvider i18n={context.i18n}>{children}</I18nProvider>;
}
