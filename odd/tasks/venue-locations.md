# Venue locations

Objective: store each venue's address and coordinates once, in their own table, so the show view can show a small map.
Branch: feat/venue-locations (from dev). Delivery: ask-on-risk. Tests: `RUN_DB_TESTS=1 .venv/bin/python -m pytest` in `server/`.

## Specs

- S1. Venues live in their own table, not in the shows table: "creo que es mas dfacil tener una tabla de coordenadas de lugares y no tenerlo dentro de la tabla de shows".
- S2. Migration creates `venues` (name, address, latitude, longitude, coords_source, updated_at), fills it with every venue already stored, and links `events.venue` to it. Existing events keep their data.
- S3. Every event saved from a scraper has its venue row; a venue saved again does not lose its coordinates.
- S4. When a ticketer gives coordinates, they are stored with `coords_source = 'ticketer'`. A `manual` row is never overwritten.
- S5. A separate step fills missing coordinates from OpenStreetMap (Nominatim), at most 1 request per second, with the contact from the environment. The to-be-confirmed placeholder is never geocoded. A failure leaves that venue without coordinates and does not stop the others.
- S6. The show API returns the venue's address and coordinates (null when unknown), and the client types are regenerated.
- Out of scope here: the map UI (needs an approved design first).

## Tasks

- T1 S1-S3 inline: migration 0007 + repository keeps venue rows. Risk item 1. Status: done, uncommitted (awaiting user OK to commit). RED 4 failing -> GREEN; mutation (venue upsert overwrites) turns test_saving_events_again_keeps_the_venue_coordinates red; full suite 779 passed with RUN_DB_TESTS=1.
- T2 S4 inline: scrapers pass coordinates through; store rule. Status: pending.
- T3 S5 inline: geocode command. Status: pending.
- T4 S6 inline: API + client types. Status: pending.

Routes: all inline (one writer, units depend on T1; no writer trigger).

## Log

- L1 (2026-11-18) User request: "podemos agregar un pequeno mapa en la vista de show con la ubicacion? algo asi [screenshot of TurboEntrada map card]". Then: "si creo que es mas dfacil tener una tabla de coordenadas de lugares y no tenerlo dentro de la tabla de shows ... que opinas" and "mandale".
- L2 Decision: the venue key is its canonical name (app/scrapers/venues.py), not name + region as first proposed. The canonical name already tells same-named venues apart (Vorterix Mar del Plata has its own name) and the venue filter uses it; region is null for some sources, so name + region would split one venue into two rows. FK `events.venue -> venues.name` ON UPDATE CASCADE, so no new id column is rewritten into every event row.
- L3 T1 done: migrations/versions/0007_venues.py (checks: coords_source in ticketer/osm/manual, both coords or none), events_repository.venues table + upsert_events inserts missing venue names ON CONFLICT DO NOTHING. Independent verifier deferred to feature end (verification timing rule). Next: commit T1 with the user's OK, then T2.
