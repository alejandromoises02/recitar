/** The app's languages: Spanish (voseo) for Spanish devices, English for every other language. */
export type Lang = "es" | "en";

export function langFromCode(code: string | null | undefined): Lang {
  if (!code) return "es";
  return code.toLowerCase().startsWith("es") ? "es" : "en";
}

/** A language saved by the web language switch; anything else means "follow the device". */
export function storedLang(value: string | null): Lang | null {
  return value === "es" || value === "en" ? value : null;
}
