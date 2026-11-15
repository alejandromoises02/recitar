import type { Lang } from "../../../../i18n/lang";
import { useLang } from "../../../../i18n/lang-context";
import { en } from "./en";
import type { ShowStrings } from "./es";
import { es } from "./es";

export type { ShowStrings };

const TABLES: Record<Lang, ShowStrings> = { es, en };

/** The show page copy in the app language. */
export function useShowStrings(): ShowStrings {
  return TABLES[useLang()];
}
