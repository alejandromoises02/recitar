import type { components } from "@/api/schema";
import type { Event } from "../domain/event";

/** An event as the API sends it (generated from its OpenAPI schema; see client/README.md). */
export type ApiEvent = components["schemas"]["Event"];

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
