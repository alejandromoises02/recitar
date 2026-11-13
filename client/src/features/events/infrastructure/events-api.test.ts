import { describe, expect, it } from "vitest";
import type { components } from "../../../api/schema";
import { ApiConfigError, ApiError, apiBaseUrl, createEventsApi } from "./events-api";

type ApiEvent = components["schemas"]["Event"];

const apiEvent = (id: string): ApiEvent => ({
  id,
  category: "concert",
  title: `Show ${id}`,
  artist: null,
  venue: "Niceto Club",
  city: "Buenos Aires",
  region: "AR-C",
  country: "AR",
  starts_at: "2026-11-14T22:00:00-03:00",
  ticket_links: [{ vendor: "Venti", url: `https://venti.live/${id}` }],
  source_url: `https://venti.live/${id}`,
  image_url: null,
  image_origin: null,
  image_author: null,
  image_license: null,
  image_source_url: null,
  updated_at: "2026-11-09T12:00:00Z",
  first_seen_at: "2026-11-02T12:00:00Z",
});

/** Answers every request with `response` and remembers the URLs asked for. */
function fakeFetch(response: () => Response) {
  const urls: string[] = [];
  const fetch = async (input: string | URL | Request) => {
    urls.push(String(input));
    return response();
  };
  return { fetch: fetch as typeof globalThis.fetch, urls };
}

const json = (body: unknown, status = 200, type = "application/json") =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": type } });

describe("listEvents", () => {
  it("sends only the filters given and maps the page", async () => {
    const { fetch, urls } = fakeFetch(() => json({ items: [apiEvent("e1")], next_cursor: "abc" }));
    const api = createEventsApi({ baseUrl: "https://api.example/", fetch });

    const page = await api.listEvents({ q: "maria becerra", venue: "Teatro Colón", category: "theatre", cursor: "xyz" });

    const url = new URL(urls[0]);
    expect(url.origin + url.pathname).toBe("https://api.example/events");
    expect(Object.fromEntries(url.searchParams)).toEqual({
      q: "maria becerra",
      venue: "Teatro Colón",
      category: "theatre",
      cursor: "xyz",
    });
    expect(page.nextCursor).toBe("abc");
    expect(page.items.map((e) => e.id)).toEqual(["e1"]);
    expect(page.items[0].startsAt).toEqual(new Date("2026-11-15T01:00:00Z"));
  });

  it("leaves out empty and missing filters", async () => {
    const { fetch, urls } = fakeFetch(() => json({ items: [], next_cursor: null }));
    const page = await createEventsApi({ baseUrl: "https://api.example", fetch }).listEvents({ q: "", venue: undefined });
    expect(urls).toEqual(["https://api.example/events"]);
    expect(page).toEqual({ items: [], nextCursor: null });
  });
});

describe("getEvent", () => {
  it("maps the event and its other dates", async () => {
    const detail = { ...apiEvent("colon-x-20261118T2000"), other_dates: [{ id: "colon-x-20261120T2000", starts_at: "2026-11-20T20:00:00-03:00" }] };
    const { fetch, urls } = fakeFetch(() => json(detail));
    const event = await createEventsApi({ baseUrl: "https://api.example", fetch }).getEvent("colon-x-20261118T2000");
    expect(urls).toEqual(["https://api.example/events/colon-x-20261118T2000"]);
    expect(event?.otherDates).toEqual([{ id: "colon-x-20261120T2000", startsAt: new Date("2026-11-20T23:00:00Z") }]);
    expect(event?.title).toBe("Show colon-x-20261118T2000");
  });

  it("escapes the id in the path", async () => {
    const { fetch, urls } = fakeFetch(() => json({ ...apiEvent("a"), other_dates: [] }));
    await createEventsApi({ baseUrl: "https://api.example", fetch }).getEvent("a/b?c");
    expect(urls).toEqual(["https://api.example/events/a%2Fb%3Fc"]);
  });

  it("is null when there is no such event", async () => {
    const problem = { type: "about:blank", title: "Event not found", status: 404, detail: "There is no event with id x." };
    const { fetch } = fakeFetch(() => json(problem, 404, "application/problem+json"));
    expect(await createEventsApi({ baseUrl: "https://api.example", fetch }).getEvent("x")).toBeNull();
  });
});

describe("listVenues", () => {
  it("maps the venues", async () => {
    const { fetch, urls } = fakeFetch(() => json({ items: [{ name: "Niceto Club", upcoming_events: 96 }] }));
    const venues = await createEventsApi({ baseUrl: "https://api.example", fetch }).listVenues();
    expect(urls).toEqual(["https://api.example/venues"]);
    expect(venues).toEqual([{ name: "Niceto Club", upcomingEvents: 96 }]);
  });
});

describe("errors", () => {
  it("turns a problem response into an ApiError with its status, title and detail", async () => {
    const problem = { type: "about:blank", title: "Invalid cursor", status: 400, detail: "Start again from the first page." };
    const { fetch } = fakeFetch(() => json(problem, 400, "application/problem+json"));
    const failure = await createEventsApi({ baseUrl: "https://api.example", fetch }).listEvents({ cursor: "bad" }).catch((e) => e);
    expect(failure).toBeInstanceOf(ApiError);
    expect([failure.status, failure.title, failure.detail]).toEqual([400, "Invalid cursor", "Start again from the first page."]);
  });

  it("still gives the status when the error body is not a problem", async () => {
    const { fetch } = fakeFetch(() => new Response("<html>Bad gateway</html>", { status: 502, statusText: "Bad Gateway" }));
    const failure = await createEventsApi({ baseUrl: "https://api.example", fetch }).listVenues().catch((e) => e);
    expect(failure).toBeInstanceOf(ApiError);
    expect([failure.status, failure.title, failure.detail]).toEqual([502, "Bad Gateway", null]);
  });

  it("lets a network failure through as it is", async () => {
    const offline = new TypeError("Network request failed");
    const fetch = (async () => {
      throw offline;
    }) as typeof globalThis.fetch;
    await expect(createEventsApi({ baseUrl: "https://api.example", fetch }).listVenues()).rejects.toBe(offline);
  });
});

describe("apiBaseUrl", () => {
  it("is the configured URL", () => {
    expect(apiBaseUrl("http://192.168.0.10:8000")).toBe("http://192.168.0.10:8000");
  });

  it.each([undefined, "", "  "])("says how to configure it when it is missing (%j)", (value) => {
    expect(() => apiBaseUrl(value)).toThrow(ApiConfigError);
    expect(() => apiBaseUrl(value)).toThrow(/EXPO_PUBLIC_API_URL/);
  });
});
