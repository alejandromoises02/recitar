import { describe, expect, it } from "vitest";
import { daysUntilLabel, imageSource, initials, shortDate } from "./show-labels";

// 15:00 UTC = 12:00 in Buenos Aires on 2026-11-13.
const NOW = new Date("2026-11-13T15:00:00Z");
const at = (iso: string) => new Date(iso);

describe("daysUntilLabel", () => {
  it.each([
    ["2026-11-13T23:00:00-03:00", "Hoy"],
    ["2026-11-14T21:00:00-03:00", "Mañana"],
    ["2026-11-15T21:00:00-03:00", "Pasado mañana"],
    ["2026-11-26T21:00:00-03:00", "En 13 días"],
  ])("%s is %s", (iso, label) => {
    expect(daysUntilLabel(at(iso), NOW)).toBe(label);
  });

  it("counts Buenos Aires days: 00:30 there is already the next day", () => {
    expect(daysUntilLabel(at("2026-11-14T00:30:00-03:00"), NOW)).toBe("Mañana");
  });

  it("counts from the Buenos Aires day of `now`, also late at night", () => {
    // 02:00 UTC on the 14th is 23:00 on the 13th in Buenos Aires.
    expect(daysUntilLabel(at("2026-11-14T21:00:00-03:00"), new Date("2026-11-14T02:00:00Z"))).toBe("Mañana");
  });
});

describe("shortDate", () => {
  it("is day and short month in Spanish, in Buenos Aires time", () => {
    expect(shortDate(at("2026-11-14T21:00:00-03:00"))).toBe("14 nov");
    expect(shortDate(at("2026-12-02T00:30:00-03:00"))).toBe("2 dic"); // stored as Dec 2 03:30 UTC
  });
});

describe("initials", () => {
  it.each([
    ["Ulises Bueno", "UB"],
    ["Richard Coleman & El Trans-Siberian Express", "RC"],
    ["La Danza de las Bestias", "LD"],
    ["BABASONICOS", "BA"],
    ["Él Mató", "ÉM"],
    ["2 Minutos", "2M"],
    ["!!!", "?"],
  ])("%s gives %s", (name, expected) => {
    expect(initials(name)).toBe(expected);
  });
});

describe("imageSource", () => {
  it("puts the API address in front of our own /media copies", () => {
    expect(imageSource("/media/a.webp", "http://192.168.0.109:8000/")).toBe("http://192.168.0.109:8000/media/a.webp");
  });

  it("keeps a full address as it is", () => {
    expect(imageSource("https://cdn.example/a.jpg", "http://x:8000")).toBe("https://cdn.example/a.jpg");
  });

  it("is null without an image", () => {
    expect(imageSource(null, "http://x:8000")).toBeNull();
  });
});
