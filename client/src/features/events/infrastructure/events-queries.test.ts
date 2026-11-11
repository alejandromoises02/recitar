import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";
import type { Event } from "../domain/event";
import type { EventsApi, EventsPage, EventsQuery } from "./events-api";
import { eventQueryOptions, eventsQueryOptions, venuesQueryOptions } from "./events-queries";

const event = (id: string) => ({ id }) as Event;

/** Serves `pages` in order, following the cursor like the real API, and remembers each request. */
function fakeApi(pages: EventsPage[]) {
  const requests: EventsQuery[] = [];
  const api: EventsApi = {
    async listEvents(query) {
      requests.push(query);
      return pages[query.cursor ? Number(query.cursor) : 0];
    },
    async getEvent(id) {
      return id === "known" ? { ...event("known"), otherDates: [] } : null;
    },
    async listVenues() {
      return [{ name: "Niceto Club", upcomingEvents: 96 }];
    },
  };
  return { api, requests };
}

describe("eventsQueryOptions", () => {
  it("follows next_cursor page by page with the same filters and stops on the last page", async () => {
    const { api, requests } = fakeApi([
      { items: [event("a"), event("b")], nextCursor: "1" },
      { items: [event("c")], nextCursor: null },
    ]);
    const client = new QueryClient();
    const options = eventsQueryOptions(api, { venue: "Niceto Club" });

    // Ask for up to 3 pages: only 2 exist, so it must stop when next_cursor is null.
    await client.fetchInfiniteQuery({ ...options, pages: 3 });

    const data = client.getQueryData(options.queryKey);
    expect(data?.pages.flatMap((p) => p.items.map((e) => e.id))).toEqual(["a", "b", "c"]);
    expect(requests).toEqual([
      { venue: "Niceto Club", cursor: undefined },
      { venue: "Niceto Club", cursor: "1" },
    ]);
  });

  it("keeps each set of filters in its own cache entry and shares one between equal filters", () => {
    const { api } = fakeApi([]);
    const niceto = eventsQueryOptions(api, { venue: "Niceto Club", q: "mila" }).queryKey;
    const sameAgain = eventsQueryOptions(api, { q: "mila", venue: "Niceto Club" }).queryKey;
    const colon = eventsQueryOptions(api, { venue: "Teatro Colón", q: "mila" }).queryKey;
    const client = new QueryClient();
    client.setQueryData(niceto, { pages: [], pageParams: [] });
    expect(client.getQueryData(sameAgain)).toEqual({ pages: [], pageParams: [] });
    expect(client.getQueryData(colon)).toBeUndefined();
  });

  it("shares the unfiltered cache entry when the filters are empty", () => {
    const { api } = fakeApi([]);
    const client = new QueryClient();
    client.setQueryData(eventsQueryOptions(api).queryKey, { pages: [], pageParams: [] });
    expect(client.getQueryData(eventsQueryOptions(api, { q: "", venue: undefined }).queryKey)).toEqual({
      pages: [],
      pageParams: [],
    });
  });
});

describe("eventQueryOptions and venuesQueryOptions", () => {
  it("read one event, null when it does not exist, and the venues", async () => {
    const { api } = fakeApi([]);
    const client = new QueryClient();
    expect((await client.fetchQuery(eventQueryOptions(api, "known")))?.id).toBe("known");
    expect(await client.fetchQuery(eventQueryOptions(api, "missing"))).toBeNull();
    expect(await client.fetchQuery(venuesQueryOptions(api))).toEqual([{ name: "Niceto Club", upcomingEvents: 96 }]);
  });
});
