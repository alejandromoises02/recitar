export type EventCategory = "concert" | "theatre" | "other";

export type TicketLink = {
  vendor: string;
  url: string;
};

export type Event = {
  id: string;
  category: EventCategory;
  artist: string;
  venue: string;
  startsAt: Date;
  ticketLinks: TicketLink[];
  sourceUrl: string;
  updatedAt: Date;
};
