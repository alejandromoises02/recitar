import type { Lang } from "../../../../i18n/lang";
import { useLang } from "../../../../i18n/lang-context";
import { en } from "./en";
import type { HomeStrings } from "./es";
import { es } from "./es";

export type { HomeStrings };

const TABLES: Record<Lang, HomeStrings> = { es, en };

/** The home copy in the device language. */
export function useStrings(): HomeStrings {
  return TABLES[useLang()];
}
