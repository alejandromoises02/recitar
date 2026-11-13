import type { components, operations } from "../../../api/schema";
import type { Event, EventDetail } from "../domain/event";
import type { Venue } from "../domain/venue";
import type { Featured, Show } from "../domain/show";
import { eventDetailFromApi, eventFromApi, featuredFromApi, showFromApi, venueFromApi } from "./event-from-api";

/** Filters and cursor of GET /events, as the API names them (see server/README.md). */
export type EventsQuery = NonNullable<operations["list_events_events_get"]["parameters"]["query"]>;

/** Filters, sort and cursor of GET /shows: the same as GET /events. */
export type ShowsQuery = NonNullable<operations["list_shows_shows_get"]["parameters"]["query"]>;

export type ShowsPage = {
  items: Show[];
  nextCursor: string | null;
};

export type EventsPage = {
  items: Event[];
  /** Pass as `cursor` to get the next page; null on the last one. */
  nextCursor: string | null;
};

export type EventsApi = {
  listEvents(query: EventsQuery): Promise<EventsPage>;
  /** null when there is no event with that id. */
  getEvent(id: string): Promise<EventDetail | null>;
  listVenues(): Promise<Venue[]>;
  /** Each show once, with all of its upcoming dates. */
  listShows(query: ShowsQuery): Promise<ShowsPage>;
  getFeatured(): Promise<Featured>;
};

/** The API answered with an error. `title` and `detail` come from its problem+json body. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly title: string,
    readonly detail: string | null,
  ) {
    super(detail ? `${title}: ${detail}` : title);
    this.name = "ApiError";
  }
}

export class ApiConfigError extends Error {
  name = "ApiConfigError";
}

/** The API's address, from EXPO_PUBLIC_API_URL (see client/README.md). */
export function apiBaseUrl(configured: string | undefined): string {
  const url = configured?.trim();
  if (!url) {
    throw new ApiConfigError(
      "Set EXPO_PUBLIC_API_URL in client/.env.local to the API's address, e.g. http://localhost:8000",
    );
  }
  return url;
}

/** RFC 7807 body of every API error (defined inline per response in the schema). */
type Problem = { title: string; detail?: string | null };

async function errorFrom(response: Response): Promise<ApiError> {
  try {
    const problem = (await response.json()) as Partial<Problem>;
    if (typeof problem.title === "string") {
      return new ApiError(response.status, problem.title, problem.detail ?? null);
    }
  } catch {
    // Not JSON (e.g. a proxy's HTML page): fall back to the status line.
  }
  return new ApiError(response.status, response.statusText || `HTTP ${response.status}`, null);
}

export function createEventsApi({ baseUrl, fetch }: { baseUrl: string; fetch: typeof globalThis.fetch }): EventsApi {
  const root = baseUrl.replace(/\/+$/, "");

  async function get<T>(path: string, params: Record<string, string | number | null | undefined> = {}): Promise<T> {
    const search = new URLSearchParams();
    for (const [name, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== "") search.set(name, String(value));
    }
    const query = search.toString();
    const response = await fetch(`${root}${path}${query ? `?${query}` : ""}`, {
      headers: { accept: "application/json" },
    });
    if (!response.ok) throw await errorFrom(response);
    return (await response.json()) as T;
  }

  return {
    async listEvents(query) {
      const page = await get<components["schemas"]["EventPage"]>("/events", query);
      return { items: page.items.map(eventFromApi), nextCursor: page.next_cursor };
    },
    async getEvent(id) {
      try {
        return eventDetailFromApi(await get<components["schemas"]["EventDetail"]>(`/events/${encodeURIComponent(id)}`));
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) return null;
        throw error;
      }
    },
    async listVenues() {
      const list = await get<components["schemas"]["VenueList"]>("/venues");
      return list.items.map(venueFromApi);
    },
    async listShows(query) {
      const page = await get<components["schemas"]["ShowPage"]>("/shows", query);
      return { items: page.items.map(showFromApi), nextCursor: page.next_cursor };
    },
    async getFeatured() {
      return featuredFromApi(await get<components["schemas"]["Featured"]>("/featured"));
    },
  };
}

let defaultApi: EventsApi | undefined;

/** The app's API client. Created on first use, so a missing URL fails the request, not the import. */
export function eventsApi(): EventsApi {
  // Expo inlines EXPO_PUBLIC_* only when read exactly like this (no destructuring).
  defaultApi ??= createEventsApi({ baseUrl: apiBaseUrl(process.env.EXPO_PUBLIC_API_URL), fetch: globalThis.fetch });
  return defaultApi;
}
