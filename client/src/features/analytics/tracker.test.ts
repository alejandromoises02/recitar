import { describe, expect, it, vi } from "vitest";
import { createTracker } from "./tracker";

const setup = (baseUrl = "https://api.example", fetch = vi.fn(async () => new Response(null, { status: 204 }))) => ({
  fetch,
  tracker: createTracker({ baseUrl, fetch: fetch as unknown as typeof globalThis.fetch, sessionId: () => "sess-12345678" }),
});
const sent = (fetch: ReturnType<typeof vi.fn>, call = 0) => {
  const [url, init] = fetch.mock.calls[call] as unknown as [string, RequestInit];
  return { url, init, body: JSON.parse(String(init.body)) };
};

describe("tracker", () => {
  it("reports a visit as a JSON POST to the API's /track with the session id", () => {
    const { tracker, fetch } = setup();
    tracker.visitStarted();
    const { url, init, body } = sent(fetch);
    expect(url).toBe("https://api.example/track");
    expect(init.method).toBe("POST");
    expect(init.headers).toEqual({ "Content-Type": "application/json" });
    expect(body).toEqual({ event: "visit started", session_id: "sess-12345678" });
  });

  it("does not double the slash when the API address ends with one", () => {
    const { tracker, fetch } = setup("http://192.168.0.109:8000/");
    tracker.visitStarted();
    expect(sent(fetch).url).toBe("http://192.168.0.109:8000/track");
  });

  it("reports the visit once, however many times it is asked", () => {
    const { tracker, fetch } = setup();
    tracker.visitStarted();
    tracker.visitStarted();
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it("reports a show opening with its key, readable name and venue", () => {
    const { tracker, fetch } = setup();
    tracker.showOpened("venti-ultraligera-en-niceto-club", "Ultraligera en Niceto Club", "Niceto Club");
    expect(sent(fetch).body).toEqual({
      event: "show opened",
      session_id: "sess-12345678",
      show_key: "venti-ultraligera-en-niceto-club",
      show_name: "Ultraligera en Niceto Club",
      venue: "Niceto Club",
    });
  });

  it("reports a filter with its value, and without one for the search", () => {
    const { tracker, fetch } = setup();
    tracker.filterUsed({ filter: "venue", value: "Niceto Club" });
    tracker.filterUsed({ filter: "search" });
    expect(sent(fetch, 0).body).toEqual({ event: "filter used", session_id: "sess-12345678", filter: "venue", value: "Niceto Club" });
    expect(sent(fetch, 1).body).toEqual({ event: "filter used", session_id: "sess-12345678", filter: "search" });
  });

  it("never gets in the way: a failing network is swallowed", async () => {
    const { tracker } = setup("https://api.example", vi.fn(async () => Promise.reject(new Error("offline"))));
    expect(() => tracker.showOpened("a-b", "A B", "V")).not.toThrow();
    await Promise.resolve();
  });

  it("never gets in the way: a fetch that throws at once is swallowed too", () => {
    const { tracker } = setup("https://api.example", vi.fn(() => { throw new Error("boom"); }));
    expect(() => tracker.visitStarted()).not.toThrow();
  });

  it("reports sharing a show, with the show's key, name and venue", () => {
    const { tracker, fetch } = setup();
    tracker.showShared("a-b", "A B", "Niceto Club");
    expect(sent(fetch).body).toEqual({ event: "show shared", session_id: "sess-12345678", show_key: "a-b", show_name: "A B", venue: "Niceto Club" });
  });

  it("reports a tap on a show listed under 'more at the venue', as that show", () => {
    const { tracker, fetch } = setup();
    tracker.moreAtVenueClicked("c-d", "C D", "Niceto Club");
    expect(sent(fetch).body).toEqual({ event: "more at venue clicked", session_id: "sess-12345678", show_key: "c-d", show_name: "C D", venue: "Niceto Club" });
  });

  it("reports an empty result with the filters that were on, leaving out what is not asked", () => {
    const { tracker, fetch } = setup();
    tracker.noResults({ filters: ["venue", "when"], venue: "Niceto Club", when: "weekend" });
    tracker.noResults({ filters: ["search"] });
    expect(sent(fetch, 0).body).toEqual({ event: "no results", session_id: "sess-12345678", filters: ["venue", "when"], venue: "Niceto Club", when: "weekend" });
    expect(sent(fetch, 1).body).toEqual({ event: "no results", session_id: "sess-12345678", filters: ["search"] });
  });
});

