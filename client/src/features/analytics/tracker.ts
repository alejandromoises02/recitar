import { configuredApiBase } from "../events/infrastructure/events-api";
import { sessionId } from "./session";

export type FilterUse = { filter: "search" | "venue" | "when" | "day" | "group"; value?: string };

export type NoResultsUse = { filters: FilterUse["filter"][]; venue?: string; when?: string };

export type Tracker = {
  visitStarted(): void;
  showOpened(showKey: string, showName: string, venue: string): void;
  showShared(showKey: string, showName: string, venue: string): void;
  moreAtVenueClicked(showKey: string, showName: string, venue: string): void;
  filterUsed(use: FilterUse): void;
  noResults(use: NoResultsUse): void;
};

type Options = { baseUrl: string; fetch: typeof globalThis.fetch; sessionId: () => string };

/** Tells the API what visitors do. Fire and forget: a failure here never reaches the person using the app. */
export function createTracker({ baseUrl, fetch, sessionId }: Options): Tracker {
  const url = `${baseUrl.replace(/\/+$/, "")}/track`;
  let visitSent = false;

  const send = (event: Record<string, string | string[]>) => {
    try {
      fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...event, session_id: sessionId() }),
      }).catch(() => undefined);
    } catch {
      // analytics never gets in the way
    }
  };

  return {
    visitStarted() {
      if (visitSent) return;
      visitSent = true;
      send({ event: "visit started" });
    },
    showOpened(showKey, showName, venue) {
      send({ event: "show opened", show_key: showKey, show_name: showName, venue });
    },
    showShared(showKey, showName, venue) {
      send({ event: "show shared", show_key: showKey, show_name: showName, venue });
    },
    moreAtVenueClicked(showKey, showName, venue) {
      send({ event: "more at venue clicked", show_key: showKey, show_name: showName, venue });
    },
    filterUsed({ filter, value }) {
      send(value === undefined ? { event: "filter used", filter } : { event: "filter used", filter, value });
    },
    noResults({ filters, venue, when }) {
      send({ event: "no results", filters, ...(venue === undefined ? {} : { venue }), ...(when === undefined ? {} : { when }) });
    },
  };
}

let defaultTracker: Tracker | undefined;

/** The app's tracker. Created on first use, so a missing API address only costs the report, not the import. */
export function tracker(): Tracker {
  try {
    defaultTracker ??= createTracker({ baseUrl: configuredApiBase(), fetch: globalThis.fetch, sessionId });
  } catch {
    return { visitStarted() {}, showOpened() {}, showShared() {}, moreAtVenueClicked() {}, filterUsed() {}, noResults() {} };
  }
  return defaultTracker;
}
