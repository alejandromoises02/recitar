# Surface brief: Home

Status: confirmed 2026-11-11 (impeccable shape). Content and behavior only; the visual design is made by the user in Figma.

## Job and audience

- Buenos Aires concert-goers checking what is new. Concerts are announced weeks or months ahead, so the question is "what was just announced?", not "what is on tonight?". Date is a filter, not the entry point.
- Mode: Operate (scanability and clarity over spectacle).
- Success: tap a show, then the official ticket link from its detail. North star: ticket clicks.

## Structure (top to bottom)

1. **Just announced**: shows first seen by the scraper recently, newest first. Updates by itself, no manual curation. Lead block.
2. **Featured**: hand-picked shows. Hidden when none are set; no filler.
3. **Full agenda**: every show, grouped by month ("Noviembre", "Diciembre"...), compact rows (date, artist, venue). Date-range and venue filters plus text search (`q`) sit above the agenda.

## Content unit: the show, not the date

- A show appears once and carries all of its upcoming dates, not only the first. How many dates the row displays (all, or the next one plus "+N") is a Figma decision; the exact date is chosen on the detail page.
- In the agenda a show sits under the month of its next date.

## Data and ranges

- Today: hundreds of shows from four venues. Agenda must handle 0 to 1000+ (cursor pagination exists).
- Must look right with missing image, missing time, `artist` null (fall back to `title`), several ticket vendors, inconsistent venue names.

## States

- First load: skeletons shaped like each block.
- API error: message + retry; show cached data when present.
- No filter results: say so and offer to clear filters.
- No just-announced shows: hide the block.

## Constraints

- Bilingual from day one: Spanish (voseo) default, English option.
- SEO: static home; every show links to its indexable URL.
- One design on iOS, Android and web; responsive from phone to desktop.

## Backend prerequisites

- `first_seen_at` per show in scraper/DB, plus a "just announced" sort or filter in the API.
- List by show instead of by date (today `/events` returns one row per date). Each show item includes every upcoming date (with its own id and ticket links), not only the first.

## Out of v1

Genre filter (data lacks it), favorites, "notify me when X is announced" alerts (strong fit with Just announced; later).

## Open for Figma

- Just announced: horizontal carousel or short list.
- Visual weight of Featured vs Just announced.
- How many days counts as "just announced" (proposed 14, tune with real data).
