# recitAR server

Python backend (FastAPI): API, scrapers and, later, AI features.

## Setup

```bash
cd server
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
playwright install chromium   # only needed to run the Movistar Arena scraper, not the tests
```

## Run

```bash
uvicorn app.main:app --reload   # http://127.0.0.1:8000/health
python -m pytest
```

## Configuration

Set `SCRAPER_CONTACT_EMAIL` in the environment (the recitAR mailbox, never a personal address;
a `+tag` alias per site, e.g. `name+wikimedia@gmail.com`, shows where a reply comes from).
It goes into the bot's User-Agent; Wikimedia blocks requests without it. Never commit the value.

## Database (Neon Postgres)

Set `DATABASE_URL` (direct) and `DATABASE_URL_POOLED` in `server/.env`. Use a Neon **dev branch**
while developing, never `production`. Tests and migrations use the direct URL; the pooled one is
for the running API.

```bash
python -m pytest                    # no database needed (database tests are skipped)
RUN_DB_TESTS=1 python -m pytest     # also runs them, in a throw-away schema that is dropped afterwards
alembic upgrade head                # create/update the tables in the database of DATABASE_URL
```

## Run the whole pipeline

```bash
python -m app.run                    # scrape every source, choose images, store the events
python -m app.run --only colon,venti # only some sources (colon, livepass, venti, movistar, ticketek, tuentrada, allaccess)
```

It applies the migrations first. A source that fails is reported and skipped; the others still
run. If a source returns less than 70% of the upcoming events already stored for it, the run
prints a `WARNING` (Movistar Arena has been seen loading only part of its listing): run it again. Needs `DATABASE_URL` and `SCRAPER_CONTACT_EMAIL` in `server/.env`, and Chromium for Movistar
Arena (`playwright install chromium`). Image copies go to `server/data/images` (ignored by git).

Venue names are normalized before saving, so one place has one name whatever the source calls
it (for example Venti's "Niceto Bar" and "Humboldt | Niceto Club" are stored as "Niceto Club").
The mapping lives in `app/scrapers/venues.py`; add new variants there.

Sources that do not say what kind of event a show is, and the music categories of those that do, go
through one provisional rule (`app/scrapers/category.py`) until LLM classification replaces it: an
all-night start (23:59) or a party word in the title is "other", a title naming another act ("tributo",
"homenaje", "experience", "covers"...) is a `tribute` unless it is orchestral ("sinfónico", "orquesta":
an homage show, kept as a concert), and anything else is a concert. The client only
shows concerts for now, so tributes are stored but not shown.

Ticketek is read through the JSON APIs its own site uses: the search with an empty query, page by
page, then one answer per show. Filtering that search by province misses shows, so it is not used.
Música and Internacionales are stored as concerts, Teatro, Especiales and Familia as theatre;
sports events are left out, and city venues that Ticketek files under the province "Buenos Aires"
are recognised by their barrio (see `app/scrapers/ticketek.py`). It reads the whole country (about
130 entries) and keeps Buenos Aires, so a run takes about six minutes at one request every two seconds.

TuEntrada is read from the pages its own site renders. Its search refuses an empty query, so the
listing is a date range from today on, page by page; then each category is listed on its own, since a
show's page does not say its category. Música, Jazz/Blues and Festivales de Música are stored as
concerts, Teatro and Familia as theatre, sports are left out, and anything else is "other". Sessions
give a city but no province, so the province comes from Georef (apis.datos.gob.ar), the government's
geography API: from the venue's coordinates when the page has them (a venue without them gets a map
pinned on the Obelisco, which is ignored), else from the city's name when only one province has a
locality by that name. Ambiguous names stay unknown and are not shown. Passes ("Abono") are not
performances. A run reads about 165 pages, so it takes about six minutes (see `app/scrapers/tuentrada.py`).

All Access is read from the pages its own site renders; its JSON API asks for an AWS WAF token and is
not used. Its search shows at most 50 results, so the listing is the home, one search per letter and
digit, and the page of every venue met along the way (which lists all of that venue's shows). The site
gives no category, so every show goes through the provisional rule; parking and other extras sold
under a show's name are left out, passes ("Abono") have no date, and a show listed twice (a VIP
package) is kept once. The province comes from Georef by the venue's coordinates, else from the
address. A run reads about 150 pages, so it takes about five minutes (see `app/scrapers/allaccess.py`).

## API

Run it with `uvicorn app.main:app --reload`; it reads the database through `DATABASE_URL_POOLED`.
Interactive docs at `/docs`, schema at `/openapi.json`.

`GET /events?limit=20&cursor=...` returns upcoming events (not started yet), ordered by start
time and then id:

```json
{"items": [{"id": "venti-...", "title": "...", "starts_at": "2026-11-13T21:00:00-03:00", "...": "..."}], "next_cursor": "eyJzdGFydHNf..."}
```

- `title` is the source's title, verbatim. `name` is that title made readable, computed on every read
  (never stored) by `app/domain/titles.py`: the trailing " en <place>" of Livepass and Venti and
  "(+18 años)" are dropped, known filler ("presenta...", "vuelve a...", "en vivo") is cut, and an
  all-caps title of several words is set in title case. Show `name` in the client.
- `artist`: the one the source gives, else read from the title by the same module when the scraper
  stores the event (`pipeline.add_artists`): the first act of several, the band of a tribute ("X por
  Y"), nothing for parties and for Teatro Colón works. It stays `null` when the title does not say
  it; the rules never guess. `tests/fixtures/titles_golden.json` holds 52 real titles with the right
  answer; `tests/test_titles.py` prints the accuracy (98% for `name`, 85% for `artist` when written)
  and fails below 90% / 80%. A future LLM extractor has to beat these numbers on the same list.
- `starts_at` comes with the Buenos Aires offset (`-03:00`), so the day and hour read as they are
  shown in Buenos Aires. It is stored in UTC; both are the same instant.
- `limit`: 1 to 100, default 20.
- `q`: search the title, the artist and the venue, up to 100 characters. Every word must appear, in any
  order, ignoring case and accents (`maria becerra` finds `María Becerra`). `%` and `_` are plain
  characters. Uses the `unaccent` extension (migration 0002); with a few hundred events no index is
  needed. Send the same `q` with every page.
- `from`, `to`: days as `YYYY-MM-DD`, both included, in **Buenos Aires** time. A show on Saturday
  at 22:00 there is stored as Sunday 01:00 UTC and still counts as Saturday. Either one can be
  left out (`from` alone: from that day on; `to` alone: until the end of that day). For one day
  send the same date in both. Only upcoming events are listed, so a `from` in the past changes
  nothing. Send the same dates with every page.
- `cursor`: the `next_cursor` of the previous page, as is (it is opaque). Leave it out for the
  first page. `next_cursor` is `null` on the last page. Paging is by key, not offset, so events
  stored while a user scrolls never make one repeat or go missing.
- `venue`: only that venue, compared exactly (send a `name` from `GET /venues` as is), up to 100
  characters. Venue names are normalized when stored (see `app/scrapers/venues.py`).
- `category`: only that kind of event: `concert`, `tribute`, `theatre`, `party` or `other`; anything else is a 422.
- `sort`: `starts_at` (default, soonest first) or `announced` (newest `first_seen_at` first, ties by
  id descending). Every event carries `first_seen_at`: the first time a scraper read it, stored
  once and never overwritten (events stored before migration 0003 got the migration time). A
  cursor only works with the `sort` that issued it; with the other one it is a 400.
- `announced_from`: a day as `YYYY-MM-DD` in Buenos Aires time; only events first seen on or after
  it. "Just announced" is `sort=announced&announced_from=<14 days ago>`.
- All filters combine (an event must match every one sent). Send the same ones with every page.

`GET /shows` lists each show once instead of once per date. A show's `id` is an event id without
its date suffix (`venti-mila-20261120T2100` belongs to `venti-mila`), compared whole. Each item has
the show's fields, taken from its next date, plus:

- `dates`: every upcoming date, soonest first, each with its event `id`, `starts_at` and
  `ticket_links`. Never empty.
- `first_seen_at`: the earliest `first_seen_at` of any of its dates, past ones included, so a new
  date of a show we already knew does not make it "just announced".

It takes the same parameters as `GET /events`. `q`, `from`, `to`, `venue` and `category` apply to
the dates: a show is listed when any upcoming date matches, and it still brings all of them.
`announced_from` and `sort=announced` look at the show's `first_seen_at`. With the default sort,
shows go by their next date, then id. Paging and cursor rules are the same.

`GET /featured` returns `{"kind": "picked" | "just_announced", "items": [...]}`: up to 10 shows in
the `GET /shows` format, all with an image. `picked` are the shows chosen by hand, in their order;
when none of them can be shown, it falls back to `just_announced`: shows first seen in the last 14
days that have an image, newest first. `?category=concert` keeps only shows of that kind in both
lists (the app sends it: it shows concerts only for now, while the database keeps every kind).

`PUT /featured` (admin only) replaces the picked list: body `{"show_ids": ["venti-mila", ...]}`,
ids from `GET /shows`, up to 20, no repeats; `[]` clears it. Every id must be a stored show, or
nothing is written (422 naming the unknown ones). It needs `Authorization: Bearer <ADMIN_TOKEN>`:

- `ADMIN_TOKEN` lives only in the server environment (`server/.env` locally), never in the repo.
  Generate it with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
- No token or a wrong one: 401. No `ADMIN_TOKEN` configured, or shorter than 32 characters: 503,
  writing is off. The token is compared in constant time and read on every request.
- Browsers cannot send it: CORS allows only GET. Call it from Postman or curl, over HTTPS once
  deployed.

`GET /venues` returns the venues that have upcoming events, by name, with how many each has:
`{"items": [{"name": "Niceto Club", "upcoming_events": 12}]}`. It is not paged (a few dozen venues);
`items` leaves room to add paging later without breaking clients. `?category=concert` counts only
events of that kind and leaves out venues with none; an unknown category is a 422.

`GET /events/{id}` returns one event with every field (ticket links, image with its credit and
licence, source), even if it already happened, plus `other_dates`: the upcoming dates of the same
show (`[{"id", "starts_at"}]`, without the event itself). An unknown id is a 404. Event ids are
`<source>-<show>-<YYYYMMDDTHHMM>`; the part before the date names the show.

`GET /go/{event_id}?v=<vendor>&from=<place>` is where every "Entradas" button points. It answers `302`
to a ticket link stored for that date (the one of `v`, else the first, else the show's page at its
source) with `utm_source=recitar`, and counts the click in `ticket_clicks` (show, date, vendor, place,
time: no IP, no user agent, no person). The destination always comes from the database, never from the
request, and only `http(s)` links without a backslash or user name are used (otherwise 404). `from` is
`show` or `spotlight` (anything else is stored as `other`); a wrong `v` or `from` is ignored, never
refused, because nothing may get between a visitor and the tickets. Crawlers and link previews are sent
on but not counted. If storing the click fails, the visitor is still sent on (it is logged).

Analytics: with `POSTHOG_API_KEY` set (the PostHog project's public token, in `server/.env`), each
counted click is also sent to PostHog as `ticket link clicked` (`show_key`, `show_name`, `event_id`,
`vendor`, `source`, `environment`), after the visitor has been sent on. `APP_ENV` (`dev` by default,
`test` or `prod`; anything else is reported as `unknown`) fills `environment`, so one dashboard can be
filtered per stage. `POSTHOG_HOST` picks the region: `https://us.i.posthog.com`
(default), `https://eu.i.posthog.com` or a self-hosted address. Events are anonymous (a random id each,
no person profile, nothing about the visitor is sent). PostHog still records the IP of the request that
reaches it, which is this server's: switch on "Discard client IP data" in the PostHog project settings.
Without the key nothing is sent. PostHog answers `200` to any key, valid or
not, so look for the events in its dashboard to know the key works. Sending waits at most 3 seconds and
a failure is only logged as a short warning (never with the key): PostHog being down never reaches a visitor.

`POST /track` is where the app reports what visitors do, for the analytics tool: a JSON body with `event`
(`visit started`, `show opened` or `filter used`), `session_id` (random, made by the app when it starts and
kept only in memory: 8 to 64 letters, digits or dashes), and, depending on the event, `show_key` and
`show_name` (a show opening needs `show_key`) or `filter` (`search`, `venue`, `when`, `day`, `group`) and
`value` (a filter event needs `filter`; for `search` the value is always dropped, so what people type is
never kept). Anything else is refused with `422`, and unknown fields too. It answers `204` and sends the
event to PostHog after answering (same settings, same failure rules as the ticket clicks); crawlers are
answered and ignored. Nothing is stored in our database. Web pages from `CORS_ORIGINS` may call it (`POST`,
`Content-Type` header only). The session id is the event's only identity: no person profile, no IP sent.
The endpoint is public, so anyone can send events; a rate limit is still to do.

`GET /media/<name>.webp` serves the image copies (`image_url` of events) from `server/data/images`,
with `Cache-Control: public, max-age=604800`. A copy never changes under its name. The folder is
local disk, so this works for development; a host without a persistent disk needs object storage
instead (see the hosting decision).

CORS: browsers may call the API from the origins in `CORS_ORIGINS` (comma-separated, e.g.
`https://recitar.example,https://www.recitar.example`). Unset, only Expo web in development
(`http://localhost:8081`, `http://127.0.0.1:8081`) is allowed. Only `GET`, no credentials.

Errors are RFC 7807 problem details (`application/problem+json`): `{"type", "title", "status",
"detail"}`, plus `errors` (one per bad parameter) on 422. A cursor this API did not issue is a
400; an out-of-range `limit`, a too-long `q`, a date that is not `YYYY-MM-DD` or a `to` before `from`
is a 422.

Versioning: only additive changes (new fields, new optional parameters) go into these paths.
A breaking change gets a new `/v2/...` path while the old one keeps working.

The client's TypeScript types are generated from this API's OpenAPI schema. After changing an
endpoint or a response model, run `python -m app.openapi_export` (writes
`client/src/api/openapi.json`), then `npm run gen:api` in `client/`. `tests/test_openapi_contract.py`
fails while the client's copy is out of date. Fields with a default (`artist`, `city`, `image_*`...)
are always sent, as `null`, so the schema lists them as required.

## Layout

- `app/api/` - HTTP endpoints, page cursors and the problem-details error format.

- `app/domain/` - core types. The client's types are generated from the API schema (see below).
- `tests/` - pytest.
