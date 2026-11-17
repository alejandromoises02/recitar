import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";
import type { Event } from "../domain/event";
import type { Show } from "../domain/show";
import type { EventsApi, EventsPage, EventsQuery, FeaturedQuery, ShowsPage, ShowsQuery, VenuesQuery } from "./events-api";
import { VISIBLE_CATEGORY } from "../application/visible-category";
import { eventQueryOptions, eventsQueryOptions, featuredQueryOptions, showQueryOptions, showsQueryOptions, venueShowsQueryOptions, venuesQueryOptions } from "./events-queries";

const event = (id: string) => ({ id }) as Event;
const show = (id: string) => ({ id }) as Show;

/** Serves `pages` in order, following the cursor like the real API, and remembers each request. */
function fakeApi(pages: EventsPage[], showPages: ShowsPage[] = []) {
  const requests: EventsQuery[] = [];
  const showRequests: ShowsQuery[] = [];
  const venueRequests: VenuesQuery[] = [];
  const featuredRequests: FeaturedQuery[] = [];
  const api: EventsApi = {
    async listEvents(query) {
      requests.push(query);
      return pages[query.cursor ? Number(query.cursor) : 0];
    },
    async getEvent(id) {
      return id === "known" ? { ...event("known"), otherDates: [] } : null;
    },
    async listVenues(query) {
      venueRequests.push(query ?? {});
      return [{ name: "Niceto Club", upcomingEvents: 96 }];
    },
    async listShows(query) {
      showRequests.push(query);
      return showPages[query.cursor ? Number(query.cursor) : 0];
    },
    async getFeatured(query) {
      featuredRequests.push(query ?? {});
      return { kind: "picked" as const, items: [show("f")] };
    },
    async getShow(id) {
      return id === "known" ? show("known") : null;
    },
  };
  return { api, requests, showRequests, venueRequests, featuredRequests };
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

describe("showsQueryOptions", () => {
  it("follows next_cursor with the same filters and sort", async () => {
    const { api, showRequests } = fakeApi([], [
      { items: [show("a")], nextCursor: "1" },
      { items: [show("b")], nextCursor: null },
    ]);
    const client = new QueryClient();
    const options = showsQueryOptions(api, { sort: "announced", announced_from: "2026-10-30" });
    const data = await client.fetchInfiniteQuery({ ...options, pages: 2 });
    expect(data.pages.flatMap((p) => p.items.map((s) => s.id))).toEqual(["a", "b"]);
    expect(showRequests.map((r) => [r.sort, r.announced_from, r.cursor])).toEqual([
      ["announced", "2026-10-30", undefined],
      ["announced", "2026-10-30", "1"],
    ]);
  });

  it("asks only for the kind of event the app shows, on every page", async () => {
    const { api, showRequests } = fakeApi([], [
      { items: [show("a")], nextCursor: "1" },
      { items: [show("b")], nextCursor: null },
    ]);
    await new QueryClient().fetchInfiniteQuery({ ...showsQueryOptions(api, { q: "rock" }), pages: 2 });
    expect(showRequests.map((r) => r.category)).toEqual(["concert", "concert"]);
  });

  it("does not share its cache with the event list", () => {
    const { api } = fakeApi([]);
    expect(showsQueryOptions(api, {}).queryKey).not.toEqual(eventsQueryOptions(api, {}).queryKey);
  });
});

describe("showQueryOptions", () => {
  it("reads one show, null when it does not exist, in its own cache entry", async () => {
    const { api } = fakeApi([]);
    const client = new QueryClient();
    expect((await client.fetchQuery(showQueryOptions(api, "known")))?.id).toBe("known");
    expect(await client.fetchQuery(showQueryOptions(api, "missing"))).toBeNull();
    expect(showQueryOptions(api, "known").queryKey).not.toEqual(eventQueryOptions(api, "known").queryKey);
  });
});

describe("featuredQueryOptions", () => {
  it("reads /featured once per key", async () => {
    const { api } = fakeApi([]);
    const featured = await new QueryClient().fetchQuery(featuredQueryOptions(api));
    expect(featured.kind).toBe("picked");
  });

  it("asks only for the kind of event the app shows", async () => {
    const { api, featuredRequests } = fakeApi([]);
    await new QueryClient().fetchQuery(featuredQueryOptions(api));
    expect(featuredRequests).toEqual([{ category: "concert" }]);
  });
});

describe("venuesQueryOptions", () => {
  it("counts only the kind of event the app shows", async () => {
    const { api, venueRequests } = fakeApi([]);
    await new QueryClient().fetchQuery(venuesQueryOptions(api));
    expect(venueRequests).toEqual([{ category: "concert" }]);
  });
});

describe("VISIBLE_CATEGORY", () => {
  it("is concerts only in this first phase", () => {
    expect(VISIBLE_CATEGORY).toBe("concert");
  });
});

describe("venueShowsQueryOptions", () => {
  it("asks for the first few shows at that venue, one more than shown so the current show can be left out", async () => {
    const { api, showRequests } = fakeApi([], [{ items: [show("a"), show("b")], nextCursor: "1" }]);
    const shows = await new QueryClient().fetchQuery(venueShowsQueryOptions(api, "Niceto Club"));
    expect(shows.map((s) => s.id)).toEqual(["a", "b"]);
    expect(showRequests).toEqual([{ venue: "Niceto Club", limit: 5, category: "concert" }]);
  });

  it("caches each venue apart from the paged listing", () => {
    const { api } = fakeApi([]);
    expect(venueShowsQueryOptions(api, "A").queryKey).not.toEqual(venueShowsQueryOptions(api, "B").queryKey);
    expect(venueShowsQueryOptions(api, "A").queryKey).not.toEqual(showsQueryOptions(api, { venue: "A" }).queryKey);
  });
});
