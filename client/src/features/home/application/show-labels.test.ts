import { describe, expect, it } from "vitest";
import { boardDate, daysUntil, daysUntilLabel, spokenDate, imageSource, initials, longDate, moreDatesLabel, shortDate } from "./show-labels";

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
    expect(daysUntilLabel(at(iso), NOW, "es")).toBe(label);
  });

  it("counts Buenos Aires days: 00:30 there is already the next day", () => {
    expect(daysUntilLabel(at("2026-11-14T00:30:00-03:00"), NOW, "es")).toBe("Mañana");
  });

  it("counts from the Buenos Aires day of `now`, also late at night", () => {
    // 02:00 UTC on the 14th is 23:00 on the 13th in Buenos Aires.
    expect(daysUntilLabel(at("2026-11-14T21:00:00-03:00"), new Date("2026-11-14T02:00:00Z"), "es")).toBe("Mañana");
  });
});

describe("daysUntil", () => {
  it.each([
    ["2026-11-13T23:00:00-03:00", 0],
    ["2026-11-14T00:30:00-03:00", 1],
    ["2026-11-26T21:00:00-03:00", 13],
  ])("%s is %i days away in Buenos Aires", (iso, days) => {
    expect(daysUntil(at(iso), NOW)).toBe(days);
  });
});

describe("shortDate", () => {
  it("is day and short month in Spanish, in Buenos Aires time", () => {
    expect(shortDate(at("2026-11-14T21:00:00-03:00"), "es")).toBe("14 nov");
    expect(shortDate(at("2026-12-02T00:30:00-03:00"), "es")).toBe("2 dic"); // stored as Dec 2 03:30 UTC
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

describe("boardDate", () => {
  it("is the Buenos Aires weekday and DD/MM when the show is this year", () => {
    expect(boardDate(at("2026-12-06T21:00:00-03:00"), NOW, "es")).toBe("DOM 06/12");
  });

  it("adds the two-digit year when the show is in another year", () => {
    expect(boardDate(at("2027-03-19T21:00:00-03:00"), NOW, "es")).toBe("VIE 19/03/27");
  });

  it("uses the Buenos Aires day: 01:00 UTC on Saturday is still Friday there", () => {
    expect(boardDate(at("2027-03-20T01:00:00Z"), NOW, "es")).toBe("VIE 19/03/27");
  });

  it("uses the Buenos Aires year: 02:00 UTC on 1 January is still 31 December there", () => {
    expect(boardDate(at("2027-01-01T02:00:00Z"), NOW, "es")).toBe("JUE 31/12");
  });

  it("writes the accented weekday", () => {
    expect(boardDate(at("2026-11-18T21:00:00-03:00"), NOW, "es")).toBe("MIÉ 18/11");
  });
});

describe("moreDatesLabel", () => {
  it.each([
    [1, ""],
    [2, "+1 fecha"],
    [4, "+3 fechas"],
  ])("a show with %i dates says %j", (count, label) => {
    expect(moreDatesLabel(count, "es")).toBe(label);
  });
});

describe("longDate", () => {
  it("is the Buenos Aires weekday and DD/MM/YYYY", () => {
    expect(longDate(at("2027-03-20T01:00:00Z"), "es")).toBe("VIE 19/03/2027");
  });
});

describe("English labels", () => {
  it("counts days in English", () => {
    expect(daysUntilLabel(at("2026-11-13T21:00:00-03:00"), NOW, "en")).toBe("Today");
    expect(daysUntilLabel(at("2026-11-14T21:00:00-03:00"), NOW, "en")).toBe("Tomorrow");
    expect(daysUntilLabel(at("2026-11-15T21:00:00-03:00"), NOW, "en")).toBe("In 2 days");
    expect(daysUntilLabel(at("2026-11-20T21:00:00-03:00"), NOW, "en")).toBe("In 7 days");
  });

  it("puts the month first in short dates", () => {
    expect(shortDate(at("2026-11-14T21:00:00-03:00"), "en")).toBe("Nov 14");
  });

  it("keeps the board's day/month order with English weekdays", () => {
    expect(boardDate(at("2026-12-06T21:00:00-03:00"), NOW, "en")).toBe("SUN 06/12");
    expect(longDate(at("2027-03-20T01:00:00Z"), "en")).toBe("FRI 19/03/2027");
  });

  it("counts more dates in English", () => {
    expect(moreDatesLabel(1, "en")).toBe("");
    expect(moreDatesLabel(2, "en")).toBe("+1 date");
    expect(moreDatesLabel(4, "en")).toBe("+3 dates");
  });
});

describe("spokenDate", () => {
  it("is the full date screen readers say, with the year only when not this year", () => {
    expect(spokenDate("2026-11-14", NOW, "es")).toBe("Sábado 14 de noviembre");
    expect(spokenDate("2027-08-28", NOW, "es")).toBe("Sábado 28 de agosto de 2027");
    expect(spokenDate("2026-11-14", NOW, "en")).toBe("Saturday, November 14");
    expect(spokenDate("2027-08-28", NOW, "en")).toBe("Saturday, August 28, 2027");
  });

  it("takes a Date as a Buenos Aires day", () => {
    expect(spokenDate(at("2026-11-15T01:00:00Z"), NOW, "es")).toBe("Sábado 14 de noviembre");
  });
});
