import { useLocales } from "expo-localization";
import type { ReactNode } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useHydrated } from "../design/hydration";
import { Platform } from "react-native";
import type { Lang } from "./lang";
import { langFromCode, storedLang } from "./lang";

const STORAGE_KEY = "recitar.lang";

type LangState = { lang: Lang; setLang: (lang: Lang) => void };

const LangContext = createContext<LangState>({ lang: "es", setLang: () => undefined });

// Browser storage can be missing or blocked (private windows, previews): then the choice lasts only this visit.
function readSaved(): Lang | null {
  if (Platform.OS !== "web") return null;
  try {
    return storedLang(window.localStorage.getItem(STORAGE_KEY));
  } catch {
    return null;
  }
}

function save(lang: Lang) {
  try {
    window.localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    // Not saved: the switch still applies until the page reloads.
  }
}

/**
 * The app language: the device's first preferred language, following changes made in system settings.
 * On web a language picked with the switch wins and is remembered; the native apps always follow the device.
 */
export function LangProvider({ children }: { children: ReactNode }) {
  const [first] = useLocales();
  const [picked, setPicked] = useState<Lang | null>(null);
  // The web build is pre-rendered without a browser, in Spanish (the shell's <html lang="es">). The first
  // browser render must match it, so the browser's language and a saved pick apply right after hydration.
  const hydrated = useHydrated();
  const lang: Lang = hydrated ? (picked ?? readSaved() ?? langFromCode(first?.languageCode)) : "es";

  useEffect(() => {
    // Screen readers and browser translation read the page language from <html lang>.
    if (Platform.OS === "web") document.documentElement.lang = lang;
  }, [lang]);

  const setLang = useCallback((next: Lang) => {
    setPicked(next);
    save(next);
  }, []);
  const value = useMemo(() => ({ lang, setLang }), [lang, setLang]);
  return <LangContext.Provider value={value}>{children}</LangContext.Provider>;
}

export const useLang = (): Lang => useContext(LangContext).lang;
export const useSetLang = () => useContext(LangContext).setLang;
