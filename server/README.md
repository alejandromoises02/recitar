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
{"items": [{"id": "venti-...", "title": "...", "starts_at": "2026-11-13T21:00:00Z", "...": "..."}], "next_cursor": "eyJzdGFydHNf..."}
```

- `limit`: 1 to 100, default 20.
- `cursor`: the `next_cursor` of the previous page, as is (it is opaque). Leave it out for the
  first page. `next_cursor` is `null` on the last page. Paging is by key, not offset, so events
  stored while a user scrolls never make one repeat or go missing.

Errors are RFC 7807 problem details (`application/problem+json`): `{"type", "title", "status",
"detail"}`, plus `errors` (one per bad parameter) on 422. A cursor this API did not issue is a
400; an out-of-range `limit` is a 422.

Versioning: only additive changes (new fields, new optional parameters) go into these paths.
A breaking change gets a new `/v2/...` path while the old one keeps working.

## Layout

- `app/api/` - HTTP endpoints, page cursors and the problem-details error format.

- `app/domain/` - core types (`Event` mirrors the client's `Event`).
- `tests/` - pytest.
