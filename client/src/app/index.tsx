import Head from "expo-router/head";
import { HomeScreen } from "@/features/home/ui/HomeScreen";
import { colors, focusRing } from "@/design/tokens";
import { useLang } from "@/i18n/lang-context";

// A visible ring on whatever has keyboard focus (WCAG 2.4.7), drawn outside the element so content never hides it.
const FOCUS_CSS = `:focus-visible { outline: ${focusRing.width}px solid ${colors.focus} !important; outline-offset: ${focusRing.offset}px !important; }`;

export default function Home() {
  const lang = useLang();
  return (
    <>
      <Head>
        <html lang={lang} />
        <title>recitAR</title>
        <style>{FOCUS_CSS}</style>
      </Head>
      <HomeScreen />
    </>
  );
}
