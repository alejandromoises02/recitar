import type { components } from "@/api/schema";
import type { Event, EventDetail } from "../domain/event";
import type { Venue } from "../domain/venue";

/** An event as the API sends it (generated from its OpenAPI schema; see client/README.md). */
export type ApiEvent = components["schemas"]["Event"];
export type ApiEventDetail = components["schemas"]["EventDetail"];
export type ApiVenue = components["schemas"]["VenueCount"];

/**
 * Turns the API's shape into the app's Event: camelCase names and real dates. Every field is
 * named here, so a field the API renames or removes stops this file from compiling.
 */
export function eventFromApi(api: ApiEvent): Event {
  return {
    id: api.id,
    category: api.category,
    title: api.title,
    artist: api.artist,
    venue: api.venue,
    city: api.city,
    region: api.region,
    country: api.country,
    startsAt: new Date(api.starts_at),
    ticketLinks: api.ticket_links.map(({ vendor, url }) => ({ vendor, url })),
    sourceUrl: api.source_url,
    imageUrl: api.image_url,
    imageOrigin: api.image_origin,
    imageAuthor: api.image_author,
    imageLicense: api.image_license,
    imageSourceUrl: api.image_source_url,
    updatedAt: new Date(api.updated_at),
  };
}

export function eventDetailFromApi(api: ApiEventDetail): EventDetail {
  return {
    ...eventFromApi(api),
    otherDates: api.other_dates.map((date) => ({ id: date.id, startsAt: new Date(date.starts_at) })),
  };
}

export function venueFromApi(api: ApiVenue): Venue {
  return { name: api.name, upcomingEvents: api.upcoming_events };
}
