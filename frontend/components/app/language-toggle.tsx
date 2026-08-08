'use client';

import { useEffect, useRef, useState } from 'react';
import Script from 'next/script';

declare global {
  interface Window {
    googleTranslateElementInit?: () => void;
    google?: any;
  }
}

const LANGUAGES: { code: string; label: string }[] = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिंदी Hindi' },
  { code: 'ta', label: 'தமிழ் Tamil' },
  { code: 'te', label: 'తెలుగు Telugu' },
  { code: 'kn', label: 'ಕನ್ನಡ Kannada' },
  { code: 'ml', label: 'മലയാളം Malayalam' },
  { code: 'mr', label: 'मराठी Marathi' },
  { code: 'bn', label: 'বাংলা Bengali' },
  { code: 'gu', label: 'ગુજરાતી Gujarati' },
  { code: 'pa', label: 'ਪੰਜਾਬੀ Punjabi' },
  { code: 'as', label: 'অসমীয়া Assamese' },
  { code: 'or', label: 'ଓଡ଼ିଆ Odia' },
];

function setLanguageCookie(code: string) {
  const value = `/en/${code}`;
  document.cookie = `googtrans=${value};path=/`;
  document.cookie = `googtrans=${value};path=/;domain=${window.location.hostname}`;
}

function clearLanguageCookie() {
  document.cookie = 'googtrans=;path=/;expires=Thu, 01 Jan 1970 00:00:00 GMT';
  document.cookie = `googtrans=;path=/;domain=${window.location.hostname};expires=Thu, 01 Jan 1970 00:00:00 GMT`;
}

function forceCleanLayout() {
  document
    .querySelectorAll('iframe.goog-te-banner-frame, iframe#\\:1\\.container, .goog-te-banner-frame')
    .forEach((el) => {
      (el as HTMLElement).style.display = 'none';
      (el as HTMLElement).style.visibility = 'hidden';
      (el as HTMLElement).style.height = '0';
    });
  document.body.style.setProperty('top', '0px', 'important');
  document.body.style.setProperty('position', 'static', 'important');
  document.documentElement.style.setProperty('top', '0px', 'important');
}

export function LanguageToggle() {
  const [current, setCurrent] = useState('en');
  const initedRef = useRef(false);

  useEffect(() => {
    window.googleTranslateElementInit = () => {
      if (initedRef.current || !window.google?.translate) return;
      initedRef.current = true;
      new window.google.translate.TranslateElement(
        {
          pageLanguage: 'en',
          includedLanguages: LANGUAGES.map((l) => l.code).join(','),
          autoDisplay: false,
        },
        'google_translate_element'
      );
    };

    const match = document.cookie.match(/googtrans=\/en\/([a-zA-Z-]+)/);
    if (match) setCurrent(match[1]);

    forceCleanLayout();

    // Watch for both new elements AND attribute changes (Google sets
    // body/html inline "top" style after the banner mounts).
    const observer = new MutationObserver(forceCleanLayout);
    observer.observe(document.documentElement, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['style'],
    });

    // Belt and braces: also run on an interval for the first few seconds,
    // since Google's banner can mount slightly after our observer starts.
    const interval = setInterval(forceCleanLayout, 300);
    const stopInterval = setTimeout(() => clearInterval(interval), 5000);

    return () => {
      observer.disconnect();
      clearInterval(interval);
      clearTimeout(stopInterval);
    };
  }, []);

  const handleChange = (code: string) => {
    setCurrent(code);

    if (code === 'en') {
      clearLanguageCookie();
      window.location.reload();
      return;
    }

    setLanguageCookie(code);
    let attempts = 0;
    const trySelect = () => {
      const combo = document.querySelector<HTMLSelectElement>('select.goog-te-combo');
      if (combo) {
        combo.value = code;
        combo.dispatchEvent(new Event('change'));
        setTimeout(forceCleanLayout, 200);
        setTimeout(forceCleanLayout, 600);
        setTimeout(forceCleanLayout, 1200);
      } else if (attempts < 20) {
        attempts += 1;
        setTimeout(trySelect, 150);
      } else {
        window.location.reload();
      }
    };
    trySelect();
  };

  return (
    <>
      <Script
        src="https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"
        strategy="afterInteractive"
      />
      <div id="google_translate_element" className="hidden" />
      <select
        value={current}
        onChange={(e) => handleChange(e.target.value)}
        aria-label="Select language"
        className="rounded-full border border-lime-600 bg-transparent px-2 py-1 text-xs text-lime-300 [&>option]:text-black"
      >
        {LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.label}
          </option>
        ))}
      </select>
    </>
  );
}