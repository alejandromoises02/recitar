# Surface brief: Home

Status: confirmed 2026-11-11 (impeccable shape); visual design chosen 2026-11-12 from code mocks (see "Chosen design").

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

## Chosen design (2026-11-12)

Reference mock: `.impeccable/mocks/home/home.html` (local only, gitignored; `home-mobile.html` previews 390 and 820 px). Discarded directions are in `.impeccable/mocks/old-designs/`. This replaces the 2026-11-11 idea of a photo carousel for Just announced.

- **Hero, desktop 40 / 60.** Left: headline "Lo nuevo en la cartelera de Buenos Aires" ("Buenos Aires" in the logo face), then **Just announced** as a split-flap marquee board: date, show name, and under the name the venue plus "+N fechas" when the show has more dates; a photo strip on the right of each row (crossed by the flap hinge), text only when there is no photo. Right: **Featured** as a fan of record sleeves (centre straight, sides tilted); a small record (64% of the sleeve) slides out of the centre sleeve. Under the fan: previous / pause / next, then a spotlight card for the centre show (Destacado tag, DD/MM/YYYY date, venue, Spotify player, ticket CTA, ticket domain, "recitAR no vende entradas" line).
- **Carousel behaviour.** Autoplay every 7 s; pauses on hover or focus; stops for good once the visitor touches, drags or uses the arrows; visible pause button; controls sit above the card so they never move; screen readers hear manual changes only.
- **Spotify sample.** The record is the play button: tapping it plays the artist's top tracks through the official compact Spotify embed (iFrame API), which stays visible in the card with Spotify's branding. The record spins only while it plays, and the carousel stops while a sample plays. Shows without a Spotify match show no player and no play badge. Spotify's 30-second `preview_url` is not available to new apps (since 2024-11-27), and hiding the embed is not allowed by Spotify's attribution rules.
- **Next up ("Próximos").** Horizontal strip of the 8 soonest shows with "en N días"; arrows on desktop, swipe on phones.
- **Explore ("Toda la cartelera").** Not a board, so it does not repeat the marquee. A sticky filter panel: text search (artist, show or venue), venue select, type chips, when chips (any date, today, this weekend, this week, this month, date range), a strip of the next 14 days (dot when a day has shows), group by month / week / day, and clear filters. Results are a grid of show cards: photo with a date block (weekday, day, month) and "+N fechas", then name, venue · time and type. Empty result: message plus clear filters. The header search jumps here with the query applied.
- **Phones and tablets.** Order: headline, Featured carousel and card, Just announced marquee, Próximos, explore. The kicker reads "Cartelera actualizada hace 3 h" there.
- **Missing image.** Typographic fallback (name or initials on a warm gradient), never an empty box.
- **Type and colour.** Logo face Alfa Slab One with stepped red/blue shadow; Unbounded for titles, Onest for text, Barlow Condensed for the marquee. Background #0E0D0C, accent #F2C230. Tokens are recorded in DESIGN.md (des03).

## Still open

- ~~Featured is empty when nobody has picked shows~~ Decided 2026-11-12: the fan shows just-announced shows that have an image (`GET /featured` returns `kind: just_announced`). The "Destacado" tag should then read as just announced.
- How many days counts as "just announced" (proposed 14, tune with real data).
- Backend for Featured (hand-picked flag) and title cleanup (artist extraction) are separate tickets.
- Spotify artist match per show and the show type (música, ópera y ballet, fiesta...) do not exist in the data yet; both need backend tickets. Check Spotify's iFrame API play/pause reliability on iOS and Android web views before building.
