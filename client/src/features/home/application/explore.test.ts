import { describe, expect, it } from "vitest";
import type { Show } from "../../events/domain/show";
import { activeFilterCount, cardDate, cardRows, daysWithShows, exploreRows, groupShows, pickedDayTile, stripDays, timeLabel, whenRange } from "./explore";

// Friday 13 November 2026, 12:00 in Buenos Aires.
const NOW = new Date("2026-11-13T15:00:00Z");
const at = (iso: string) => new Date(iso);

const show = (id: string, starts: string[]): Show => ({
  id,
  category: "concert",
  title: id,
  name: id,
  artist: null,
  venue: "V",
  city: null,
  region: null,
  country: null,
  sourceUrl: "https://example.com",
  imageUrl: null,
  imageOrigin: null,
  imageAuthor: null,
  imageLicense: null,
  imageSourceUrl: null,
  firstSeenAt: at("2026-11-01T12:00:00Z"),
  dates: starts.map((iso, i) => ({ id: `${id}-${i}`, startsAt: at(iso), ticketLinks: [] })),
});

describe("whenRange", () => {
  it.each([
    ["all", {}],
    ["today", { from: "2026-11-13", to: "2026-11-13" }],
    ["weekend", { from: "2026-11-13", to: "2026-11-15" }],
    ["week", { from: "2026-11-13", to: "2026-11-15" }],
    ["month", { from: "2026-11-13", to: "2026-11-30" }],
  ] as const)("%s on a Friday is %j", (when, range) => {
    expect(whenRange(when, NOW)).toEqual(range);
  });

  it("starts the weekend on Friday when today is earlier in the week", () => {
    const tuesday = at("2026-11-10T15:00:00Z");
    expect(whenRange("weekend", tuesday)).toEqual({ from: "2026-11-13", to: "2026-11-15" });
    expect(whenRange("week", tuesday)).toEqual({ from: "2026-11-10", to: "2026-11-15" });
  });

  it("is one day for a picked day", () => {
    expect(whenRange("day", NOW, "2026-11-20")).toEqual({ from: "2026-11-20", to: "2026-11-20" });
  });

  it("uses the Buenos Aires day: 01:00 UTC Saturday is still Friday there", () => {
    expect(whenRange("today", at("2026-11-14T01:00:00Z"))).toEqual({ from: "2026-11-13", to: "2026-11-13" });
  });
});

describe("stripDays", () => {
  it("is today and the next 6 days, today labelled HOY", () => {
    const days = stripDays(NOW, "es");
    expect(days).toHaveLength(7);
    expect(days[0]).toEqual({ iso: "2026-11-13", label: "HOY", day: 13 });
    expect(days[1]).toEqual({ iso: "2026-11-14", label: "SÁB", day: 14 });
    expect(days[6].iso).toBe("2026-11-19");
  });
});

describe("pickedDayTile", () => {
  it("is the weekday, day and month of a day picked this year", () => {
    expect(pickedDayTile("2026-12-24", NOW, "es")).toEqual({ iso: "2026-12-24", label: "JUE", day: 24, month: "DIC" });
  });

  it("adds the two-digit year to the month for another year", () => {
    expect(pickedDayTile("2027-08-28", NOW, "es")).toEqual({ iso: "2027-08-28", label: "SÁB", day: 28, month: "AGO 27" });
  });
});

describe("English dates", () => {
  const shows = [
    show("today", ["2026-11-13T21:00:00-03:00"]),
    show("tomorrow", ["2026-11-14T21:00:00-03:00"]),
    show("december", ["2026-12-01T21:00:00-03:00"]),
  ];

  it("titles days, weeks and months in English", () => {
    expect(groupShows(shows, "day", NOW, "en", {}).map((g) => [g.title, g.note])).toEqual([
      ["Friday, November 13", "Today"],
      ["Saturday, November 14", "Tomorrow"],
      ["Tuesday, December 1", null],
    ]);
    expect(groupShows(shows, "week", NOW, "en", {}).map((g) => [g.title, g.note])).toEqual([
      ["Week of November 9–15", "this week"],
      ["Week of November 30 – December 6", null],
    ]);
    expect(groupShows(shows, "month", NOW, "en", {}).map((g) => g.title)).toEqual(["November 2026", "December 2026"]);
  });

  it("labels the day strip, picked day and cards in English", () => {
    const days = stripDays(NOW, "en");
    expect(days[0].label).toBe("TODAY");
    expect(days[1].label).toBe("SAT");
    expect(pickedDayTile("2027-08-28", NOW, "en")).toEqual({ iso: "2027-08-28", label: "SAT", day: 28, month: "AUG 27" });
    expect(cardDate(at("2026-11-14T01:00:00Z"), "en")).toEqual({ weekday: "FRI", day: 13, month: "NOV" });
  });

  it("gives day blocks English weekday, month and note", () => {
    const [today] = groupShows(shows, "month", NOW, "en", {})[0].days;
    expect(today).toMatchObject({ weekday: "FRI", month: "NOV", note: "Today" });
  });
});

describe("daysWithShows", () => {
  it("collects the Buenos Aires day of every date", () => {
    const set = daysWithShows([show("a", ["2026-11-14T23:00:00-03:00", "2026-11-20T21:00:00-03:00"]), show("b", ["2026-11-15T01:30:00Z"])]);
    expect([...set].sort()).toEqual(["2026-11-14", "2026-11-20"]);
  });
});

describe("groupShows", () => {
  const shows = [
    show("today", ["2026-11-13T21:00:00-03:00"]),
    show("tomorrow", ["2026-11-14T21:00:00-03:00"]),
    show("next-week", ["2026-11-18T21:00:00-03:00"]),
    show("december", ["2026-12-01T21:00:00-03:00"]),
  ];

  it("groups by month, in date order", () => {
    const groups = groupShows(shows, "month", NOW, "es", {});
    expect(groups.map((g) => [g.title, g.days.flatMap((d) => d.items.map((i) => i.show.id))])).toEqual([
      ["Noviembre 2026", ["today", "tomorrow", "next-week"]],
      ["Diciembre 2026", ["december"]],
    ]);
  });

  it("groups by week from Monday to Sunday and marks this week", () => {
    const groups = groupShows(shows, "week", NOW, "es", {});
    expect(groups.map((g) => [g.title, g.note])).toEqual([
      ["Semana del 9 al 15 de noviembre", "esta semana"],
      ["Semana del 16 al 22 de noviembre", null],
      ["Semana del 30 de noviembre al 6 de diciembre", null],
    ]);
  });

  it("groups by day and marks today and tomorrow", () => {
    const groups = groupShows(shows, "day", NOW, "es", {});
    expect(groups.map((g) => [g.title, g.note, g.days.length])).toEqual([
      ["Viernes 13 de noviembre", "Hoy", 1],
      ["Sábado 14 de noviembre", "Mañana", 1],
      ["Miércoles 18 de noviembre", null, 1],
      ["Martes 1 de diciembre", null, 1],
    ]);
  });

  it("splits each group into one block per day, in date order, with Hoy and Mañana", () => {
    const sameDay = show("same-day", ["2026-11-14T18:00:00-03:00"]);
    const [november] = groupShows([...shows, sameDay], "month", NOW, "es", {});
    expect(november.count).toBe(4);
    expect(november.days.map((d) => [d.iso, d.weekday, d.day, d.month, d.note, d.items.map((i) => i.show.id)])).toEqual([
      ["2026-11-13", "VIE", 13, "NOV", "Hoy", ["today"]],
      ["2026-11-14", "SÁB", 14, "NOV", "Mañana", ["same-day", "tomorrow"]],
      ["2026-11-18", "MIÉ", 18, "NOV", null, ["next-week"]],
    ]);
  });

  it("lists a show once for every date it has, each under its own day", () => {
    const multi = show("multi", ["2026-11-13T21:00:00-03:00", "2026-11-14T21:00:00-03:00", "2026-12-05T21:00:00-03:00"]);
    const groups = groupShows([multi], "day", NOW, "es", {});
    expect(groups.map((g) => [g.title, g.days[0].items.map((i) => i.show.id)])).toEqual([
      ["Viernes 13 de noviembre", ["multi"]],
      ["Sábado 14 de noviembre", ["multi"]],
      ["Sábado 5 de diciembre", ["multi"]],
    ]);
  });

  it("keeps only the dates inside the range", () => {
    const multi = show("multi", ["2026-11-14T21:00:00-03:00", "2026-12-05T21:00:00-03:00"]);
    const groups = groupShows([multi], "month", NOW, "es", { from: "2026-12-01", to: "2026-12-31" });
    expect(groups.map((g) => g.title)).toEqual(["Diciembre 2026"]);
    expect(groups[0].days[0].items[0].date).toEqual(at("2026-12-05T21:00:00-03:00"));
  });

  it("leaves out dates after the horizon, where shows not loaded yet could still come", () => {
    const multi = show("multi", ["2026-11-13T21:00:00-03:00", "2026-12-05T21:00:00-03:00"]);
    const groups = groupShows([multi], "day", NOW, "es", {}, at("2026-11-20T21:00:00-03:00"));
    expect(groups.map((g) => g.title)).toEqual(["Viernes 13 de noviembre"]);
  });

  it("gives each date its own item key, so a show twice on one day stays two items", () => {
    const twice = show("twice", ["2026-11-13T18:00:00-03:00", "2026-11-13T21:00:00-03:00"]);
    const [day] = groupShows([twice], "day", NOW, "es", {});
    expect(day.days[0].items.map((i) => i.key)).toEqual(["twice-0", "twice-1"]);
  });
});

describe("cardDate and timeLabel", () => {
  it("is the weekday, day and short month in Buenos Aires", () => {
    expect(cardDate(at("2026-11-14T01:00:00Z"), "es")).toEqual({ weekday: "VIE", day: 13, month: "NOV" });
  });

  it("is HH:MM in Buenos Aires", () => {
    expect(timeLabel(at("2026-11-14T00:30:00Z"))).toBe("21:30");
  });
});

describe("exploreRows", () => {
  const shows = [
    show("a", ["2026-11-13T21:00:00-03:00"]),
    show("b", ["2026-11-14T21:00:00-03:00"]),
    show("c", ["2026-11-18T21:00:00-03:00"]),
    show("d", ["2026-12-01T21:00:00-03:00"]),
  ];
  const groups = groupShows(shows, "month", NOW, "es", {});

  it("is one title row per group, then its day blocks one per row on phones", () => {
    const rows = exploreRows(groups, 1);
    expect(rows.map((r) => (r.kind === "group" ? `# ${r.title}` : r.kind === "days" ? r.blocks.map((b) => b.iso).join(",") : "?"))).toEqual([
      "# Noviembre 2026",
      "2026-11-13",
      "2026-11-14",
      "2026-11-18",
      "# Diciembre 2026",
      "2026-12-01",
    ]);
  });

  it("puts several day blocks in a row on wide screens, never mixing groups", () => {
    const rows = exploreRows(groups, 2);
    expect(rows.map((r) => (r.kind === "group" ? `# ${r.title}` : r.kind === "days" ? r.blocks.map((b) => b.iso).join(",") : "?"))).toEqual([
      "# Noviembre 2026",
      "2026-11-13,2026-11-14",
      "2026-11-18",
      "# Diciembre 2026",
      "2026-12-01",
    ]);
  });

  it("gives every row a unique key", () => {
    const keys = exploreRows(groups, 2).map((r) => r.key);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it("keeps a collapsed group's title, marked collapsed, and leaves out its day blocks", () => {
    const rows = exploreRows(groups, 1, new Set(["2026-11"]));
    expect(rows.map((r) => (r.kind === "group" ? `# ${r.title} ${r.expanded ? "open" : "closed"}` : r.kind === "days" ? r.blocks.map((b) => b.iso).join(",") : "?"))).toEqual([
      "# Noviembre 2026 closed",
      "# Diciembre 2026 open",
      "2026-12-01",
    ]);
  });

  it("names the group on its title row so it can be toggled, and still counts the hidden shows", () => {
    const [title] = exploreRows(groups, 1, new Set(["2026-11"]));
    expect(title).toMatchObject({ kind: "group", group: "2026-11", count: 3, expanded: false });
  });
});

describe("cardRows", () => {
  const shows = [
    show("a", ["2026-11-13T21:00:00-03:00"]),
    show("b", ["2026-11-13T22:00:00-03:00"]),
    show("c", ["2026-11-18T21:00:00-03:00"]),
    show("d", ["2026-12-01T21:00:00-03:00"]),
  ];
  const groups = groupShows(shows, "month", NOW, "es", {});

  it("is each group's title, then its shows as cards `columns` per row across days", () => {
    const rows = cardRows(groups, 2);
    expect(rows.map((r) => (r.kind === "group" ? `# ${r.title}` : r.kind === "cards" ? r.items.map((i) => i.show.id).join(",") : "?"))).toEqual([
      "# Noviembre 2026",
      "a,b",
      "c",
      "# Diciembre 2026",
      "d",
    ]);
  });

  it("gives every row a unique key", () => {
    const keys = cardRows(groups, 1).map((r) => r.key);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it("keeps a collapsed group's title and leaves out its cards", () => {
    const rows = cardRows(groups, 2, new Set(["2026-12"]));
    expect(rows.map((r) => (r.kind === "group" ? `# ${r.title} ${r.expanded ? "open" : "closed"}` : r.kind === "cards" ? r.items.map((i) => i.show.id).join(",") : "?"))).toEqual([
      "# Noviembre 2026 open",
      "a,b",
      "c",
      "# Diciembre 2026 closed",
    ]);
  });
});

describe("activeFilterCount", () => {
  const none = { text: "", venue: null, when: "all" as const };

  it("is zero with no filters", () => {
    expect(activeFilterCount(none)).toBe(0);
  });

  it("counts search, venue and date, ignoring blank search", () => {
    expect(activeFilterCount({ ...none, text: "   " })).toBe(0);
    expect(activeFilterCount({ text: "jazz", venue: "Niceto Club", when: "weekend" })).toBe(3);
    expect(activeFilterCount({ ...none, when: "day" })).toBe(1);
  });
});
