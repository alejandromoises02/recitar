export type EventCategory = "concert" | "theatre" | "other";

export type TicketLink = {
  vendor: string;
  url: string;
};

export type Event = {
  id: string;
  category: EventCategory;
  title: string;
  artist: string | null;
  venue: string;
  city: string | null;
  /** ISO 3166-2 subdivision, e.g. "AR-C" (Ciudad de Buenos Aires). */
  region: string | null;
  /** ISO 3166-1 alpha-2, e.g. "AR". */
  country: string | null;
  startsAt: Date;
  ticketLinks: TicketLink[];
  sourceUrl: string;
  updatedAt: Date;
};
