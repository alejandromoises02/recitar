export type Venue = {
  /** Exact name to filter events by. */
  name: string;
  upcomingEvents: number;
};

/** What the API stores a show at while its venue is not confirmed yet (server: domain.event.VENUE_TO_BE_CONFIRMED). */
export const VENUE_TO_BE_CONFIRMED = "Lugar a confirmar";
