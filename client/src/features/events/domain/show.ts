import type { EventCategory, ImageOrigin, TicketLink } from "./event";

/** One upcoming date of a show, with where to buy it. */
export type ShowDateTickets = {
  id: string;
  startsAt: Date;
  ticketLinks: TicketLink[];
};

/** A show once, with all of its upcoming dates (soonest first, never empty). Display fields come
 * from its next date. Show `name` in the UI; `title` is the source's words. */
export type Show = {
  /** The show key: an event id without its date. */
  id: string;
  category: EventCategory;
  title: string;
  name: string;
  artist: string | null;
  venue: string;
  city: string | null;
  region: string | null;
  country: string | null;
  sourceUrl: string;
  imageUrl: string | null;
  imageOrigin: ImageOrigin | null;
  imageAuthor: string | null;
  imageLicense: string | null;
  imageSourceUrl: string | null;
  /** First time any of its dates was seen: when we learned it was announced. */
  firstSeenAt: Date;
  /** Last time a scraper read any of its upcoming dates ("actualizado hace X"). */
  updatedAt: Date;
  dates: ShowDateTickets[];
};

/** What the home's record fan shows: hand-picked shows, or just-announced ones with an image. */
export type Featured = {
  kind: "picked" | "just_announced";
  items: Show[];
};
