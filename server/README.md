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
python -m app.run --only colon,venti # only some sources (colon, livepass, venti, movistar)
```

It applies the migrations first. A source that fails is reported and skipped; the others still
run. If a source returns less than 70% of the upcoming events already stored for it, the run
prints a `WARNING` (Movistar Arena has been seen loading only part of its listing): run it again. Needs `DATABASE_URL` and `SCRAPER_CONTACT_EMAIL` in `server/.env`, and Chromium for Movistar
Arena (`playwright install chromium`). Image copies go to `server/data/images` (ignored by git).

## API

Run it with `uvicorn app.main:app --reload`; it reads the database through `DATABASE_URL_POOLED`.
Interactive docs at `/docs`, schema at `/openapi.json`.

`GET /events?limit=20&cursor=...` returns upcoming events (not started yet), ordered by start
time and then id:

```json
{"items": [{"id": "venti-...", "title": "...", "starts_at": "2026-11-13T21:00:00-03:00", "...": "..."}], "next_cursor": "eyJzdGFydHNf..."}
```

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

`GET /events/{id}` returns one event with every field (ticket links, image with its credit and
licence, source), even if it already happened, plus `other_dates`: the upcoming dates of the same
show (`[{"id", "starts_at"}]`, without the event itself). An unknown id is a 404. Event ids are
`<source>-<show>-<YYYYMMDDTHHMM>`; the part before the date names the show.

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

## Layout

- `app/api/` - HTTP endpoints, page cursors and the problem-details error format.

- `app/domain/` - core types (`Event` mirrors the client's `Event`).
- `tests/` - pytest.
