export type EventCategory = "concert" | "theatre" | "party" | "other";

/**
 * Where an image comes from. Only "source" is unlicensed: the image the ticket seller publishes,
 * shown straight from there. Before a public launch every "source" image must be replaced.
 */
export type ImageOrigin = "source" | "licensed" | "venue";

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
  imageUrl: string | null;
  imageOrigin: ImageOrigin | null;
  /** Credit, required by most free licences. */
  imageAuthor: string | null;
  /** e.g. "CC BY-SA 4.0". */
  imageLicense: string | null;
  /** Page where the image and its licence are published. */
  imageSourceUrl: string | null;
  updatedAt: Date;
};
