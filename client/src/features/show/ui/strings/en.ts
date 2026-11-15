import type { ShowStrings } from "./es";

export const en: ShowStrings = {
  back: "All shows",
  backLabel: "Back to all shows",
  dates: (count) => (count === 1 ? "1 date" : `${count} dates`),
  categories: { concert: "Concert", theatre: "Theatre", party: "Party", other: "Show" },
  pickDate: "Pick a date",
  tickets: "Tickets",
  ticketsAt: "Tickets at",
  ticketsVendor: (vendor) => `Tickets at ${vendor}`,
  opensNewTab: "Opens in a new tab.",
  trust: "recitAR doesn't sell tickets: it takes you to each show's official page.",
  dataFrom: "Data from",
  photo: "Photo",
  share: "Share this show",
  linkCopied: "Link copied",
  loading: "Loading the show…",
  loadFailed: "We couldn't load this show.",
  retry: "Try again",
  notFoundTitle: "We can't find this show",
  notFoundBody: "It may be over, or the link may be wrong.",
  goToListing: "See all shows",
};
