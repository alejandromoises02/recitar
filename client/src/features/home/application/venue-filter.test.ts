import { describe, expect, it } from "vitest";
import type { Venue } from "../../events/domain/venue";
import { matchingVenues, toggleVenue, venueChips } from "./venue-filter";

const venue = (name: string, upcomingEvents: number): Venue => ({ name, upcomingEvents });
const VENUES = [
  venue("Club Ciudad", 2),
  venue("Movistar Arena", 74),
  venue("Niceto Club", 64),
  venue("Teatro Colón", 18),
  venue("Teatro Gran Rex", 41),
  venue("The Roxy Live", 21),
];

describe("venueChips", () => {
  it("is the venues with the most upcoming dates, most first, up to the limit", () => {
    expect(venueChips(VENUES, [], 3)).toEqual(["Movistar Arena", "Niceto Club", "Teatro Gran Rex"]);
  });

  it("breaks a tie by name", () => {
    expect(venueChips([venue("B", 5), venue("A", 5)], [], 2)).toEqual(["A", "B"]);
  });

  it("puts the chosen venues first when they are not among them, so the filter in use is always seen", () => {
    expect(venueChips(VENUES, ["The Roxy Live", "Club Ciudad"], 3)).toEqual([
      "The Roxy Live", "Club Ciudad", "Movistar Arena", "Niceto Club", "Teatro Gran Rex",
    ]);
  });

  it("leaves a chosen venue that is already shown where it is", () => {
    expect(venueChips(VENUES, ["Niceto Club"], 3)).toEqual(["Movistar Arena", "Niceto Club", "Teatro Gran Rex"]);
  });
});

describe("matchingVenues", () => {
  it("is every venue by name when nothing is typed", () => {
    expect(matchingVenues(VENUES, "  ").map((v) => v.name)).toEqual([
      "Club Ciudad", "Movistar Arena", "Niceto Club", "Teatro Colón", "Teatro Gran Rex", "The Roxy Live",
    ]);
  });

  it("matches any part of the name ignoring case and accents", () => {
    expect(matchingVenues(VENUES, "COLON").map((v) => v.name)).toEqual(["Teatro Colón"]);
    expect(matchingVenues(VENUES, "club").map((v) => v.name)).toEqual(["Club Ciudad", "Niceto Club"]);
  });

  it("is empty when no venue has that name", () => {
    expect(matchingVenues(VENUES, "luna park")).toEqual([]);
  });
});

describe("toggleVenue", () => {
  it("adds a venue that is not chosen, after the others", () => {
    expect(toggleVenue(["Estadio River Plate"], "Estadio Huracán")).toEqual(["Estadio River Plate", "Estadio Huracán"]);
  });

  it("removes a venue that is chosen", () => {
    expect(toggleVenue(["Estadio River Plate", "Estadio Huracán"], "Estadio River Plate")).toEqual(["Estadio Huracán"]);
  });
});
