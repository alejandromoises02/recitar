/** Small texts and values the home's show cards show. Days are Buenos Aires days. */

const BUENOS_AIRES = "America/Argentina/Buenos_Aires";
const DAY = new Intl.DateTimeFormat("en-CA", { timeZone: BUENOS_AIRES, year: "numeric", month: "2-digit", day: "2-digit" });
const MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

/** Days since 1970 of the Buenos Aires calendar day `date` falls on. */
function dayNumber(date: Date): number {
  const [year, month, day] = DAY.format(date).split("-").map(Number);
  return Date.UTC(year, month - 1, day) / 86_400_000;
}

export function daysUntilLabel(startsAt: Date, now: Date): string {
  const days = dayNumber(startsAt) - dayNumber(now);
  if (days <= 0) return "Hoy";
  if (days === 1) return "Mañana";
  if (days === 2) return "Pasado mañana";
  return `En ${days} días`;
}

/** "14 nov": day and short month in Spanish, in Buenos Aires time. */
export function shortDate(startsAt: Date): string {
  const [, month, day] = DAY.format(startsAt).split("-").map(Number);
  return `${day} ${MONTHS[month - 1]}`;
}

const ALNUM = /[\p{L}\p{N}]/u;

/** Two characters for a show without a photo: the first of its first two words, or the first two
 * of a single word. "?" when the name has no letters or digits. */
export function initials(name: string): string {
  const words = name.split(/\s+/).filter((word) => ALNUM.test(word));
  const chars =
    words.length >= 2
      ? words.slice(0, 2).map((word) => word.match(ALNUM)![0])
      : [...(words[0] ?? "")].filter((c) => ALNUM.test(c)).slice(0, 2);
  return chars.length ? chars.join("").toLocaleUpperCase("es") : "?";
}

/** Where to load an image from: our own copies come as "/media/..." on the API. */
export function imageSource(imageUrl: string | null, apiBase: string): string | null {
  if (!imageUrl) return null;
  if (/^https?:\/\//.test(imageUrl)) return imageUrl;
  return `${apiBase.replace(/\/+$/, "")}${imageUrl.startsWith("/") ? "" : "/"}${imageUrl}`;
}
