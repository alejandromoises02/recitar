import { Platform } from "react-native";
import type { Lang } from "../../../i18n/lang";
import { useLang, useSetLang } from "../../../i18n/lang-context";
import { Segmented } from "./controls/Segmented";
import { useStrings } from "./strings";

// Each language is named in itself, so it can be found whatever language the page is in.
const OPTIONS: { value: Lang; label: string; accessibilityLabel: string }[] = [
  { value: "es", label: "ES", accessibilityLabel: "Español" },
  { value: "en", label: "EN", accessibilityLabel: "English" },
];

/** Web only: browsers often ask for a language their user does not want here. The apps follow the phone. */
export function LangSwitch() {
  const lang = useLang();
  const setLang = useSetLang();
  const strings = useStrings();
  if (Platform.OS !== "web") return null;
  return <Segmented options={OPTIONS} value={lang} onChange={setLang} accessibilityLabel={strings.language} />;
}
