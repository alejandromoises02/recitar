import type { Lang } from "../../../i18n/lang";

/** Calendar words and the date formats that change their order with the language. */
export type DateWords = {
  weekdays: readonly string[];
  weekdaysShort: readonly string[];
  months: readonly string[];
  monthsShort: readonly string[];
  todayShort: string;
  today: string;
  tomorrow: string;
  thisWeek: string;
  daysUntil: (days: number) => string;
  moreDates: (more: number) => string;
  /** "Sábado 14 de noviembre" / "Saturday, November 14". */
  dayTitle: (weekday: number, day: number, month: number) => string;
  /** Monday to Sunday of one week; months are 1-based. */
  weekTitle: (from: { day: number; month: number }, to: { day: number; month: number }) => string;
  monthTitle: (month: number, year: number) => string;
  /** `dayTitle` plus the year: "Sábado 28 de agosto de 2027" / "Saturday, August 28, 2027". */
  withYear: (title: string, year: number) => string;
  shortDate: (day: number, month: number) => string;
};

const capitalise = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);
const upperShort = (months: readonly string[]) => months.map((m) => m.slice(0, 3).toUpperCase());

const ES_MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
const EN_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const ES_WEEKDAYS = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"];
const EN_WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

const es: DateWords = {
  weekdays: ES_WEEKDAYS,
  weekdaysShort: ["DOM", "LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB"],
  months: ES_MONTHS,
  monthsShort: upperShort(ES_MONTHS),
  todayShort: "HOY",
  today: "Hoy",
  tomorrow: "Mañana",
  thisWeek: "esta semana",
  daysUntil: (days) => (days <= 0 ? "Hoy" : days === 1 ? "Mañana" : days === 2 ? "Pasado mañana" : `En ${days} días`),
  moreDates: (more) => (more <= 0 ? "" : `+${more} ${more === 1 ? "fecha" : "fechas"}`),
  dayTitle: (weekday, day, month) => `${ES_WEEKDAYS[weekday]} ${day} de ${ES_MONTHS[month - 1]}`,
  weekTitle: (from, to) => {
    const start = from.month === to.month ? `${from.day}` : `${from.day} de ${ES_MONTHS[from.month - 1]}`;
    return `Semana del ${start} al ${to.day} de ${ES_MONTHS[to.month - 1]}`;
  },
  monthTitle: (month, year) => `${capitalise(ES_MONTHS[month - 1])} ${year}`,
  withYear: (title, year) => `${title} de ${year}`,
  shortDate: (day, month) => `${day} ${ES_MONTHS[month - 1].slice(0, 3)}`,
};

const en: DateWords = {
  weekdays: EN_WEEKDAYS,
  weekdaysShort: ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"],
  months: EN_MONTHS,
  monthsShort: upperShort(EN_MONTHS),
  todayShort: "TODAY",
  today: "Today",
  tomorrow: "Tomorrow",
  thisWeek: "this week",
  daysUntil: (days) => (days <= 0 ? "Today" : days === 1 ? "Tomorrow" : `In ${days} days`),
  moreDates: (more) => (more <= 0 ? "" : `+${more} ${more === 1 ? "date" : "dates"}`),
  dayTitle: (weekday, day, month) => `${EN_WEEKDAYS[weekday]}, ${EN_MONTHS[month - 1]} ${day}`,
  weekTitle: (from, to) =>
    from.month === to.month
      ? `Week of ${EN_MONTHS[from.month - 1]} ${from.day}–${to.day}`
      : `Week of ${EN_MONTHS[from.month - 1]} ${from.day} – ${EN_MONTHS[to.month - 1]} ${to.day}`,
  monthTitle: (month, year) => `${EN_MONTHS[month - 1]} ${year}`,
  withYear: (title, year) => `${title}, ${year}`,
  shortDate: (day, month) => `${EN_MONTHS[month - 1].slice(0, 3)} ${day}`,
};

export const DATE_WORDS: Record<Lang, DateWords> = { es, en };
