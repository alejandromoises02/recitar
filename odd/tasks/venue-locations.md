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

- T1 S1-S3 inline: migration 0007 + repository keeps venue rows. Risk item 1. Status: done, commit 9153cab. RED 4 failing -> GREEN; mutation (venue upsert overwrites) turns test_saving_events_again_keeps_the_venue_coordinates red; full suite 779 passed with RUN_DB_TESTS=1.
- T2 S4 inline: scrapers pass coordinates through; store rule. Status: done, uncommitted (awaiting user OK). RED 6 -> GREEN; mutations: placeholder guard -> test_a_venue_to_be_confirmed_never_gets_coordinates red, manual guard -> test_ticketer_coordinates_replace_geocoded_ones_but_never_manual_ones red; full suite 786 passed (RUN_DB_TESTS=1).
- T3 S5 inline: geocode command. Status: done, uncommitted (awaiting user OK). RED (module missing) -> GREEN 7; mutations: region check, not-a-place check, manual filter each turn a test red; full suite 793 passed (RUN_DB_TESTS=1). Not yet run against the dev database.
- T4 S6 inline: API + client types. Status: done, uncommitted (awaiting user OK). RED (ShowDetail/VenueLocation missing) -> GREEN; full server suite 798 passed (RUN_DB_TESTS=1); client tsc exit 0, vitest 261 passed.

Routes: all inline (one writer, units depend on T1; no writer trigger).

## Log

- L1 (2026-11-18) User request: "podemos agregar un pequeno mapa en la vista de show con la ubicacion? algo asi [screenshot of TurboEntrada map card]". Then: "si creo que es mas dfacil tener una tabla de coordenadas de lugares y no tenerlo dentro de la tabla de shows ... que opinas" and "mandale".
- L2 Decision: the venue key is its canonical name (app/scrapers/venues.py), not name + region as first proposed. The canonical name already tells same-named venues apart (Vorterix Mar del Plata has its own name) and the venue filter uses it; region is null for some sources, so name + region would split one venue into two rows. FK `events.venue -> venues.name` ON UPDATE CASCADE, so no new id column is rewritten into every event row.
- L3 T1 done: migrations/versions/0007_venues.py (checks: coords_source in ticketer/osm/manual, both coords or none), events_repository.venues table + upsert_events inserts missing venue names ON CONFLICT DO NOTHING. Independent verifier deferred to feature end (verification timing rule). Next: commit T1 with the user's OK, then T2.
- L4 (2026-11-18) User: "si az commit" -> T1 committed as 9153cab.
- L5 T2: Event.venue_point (Field exclude=True: not stored on events, not in OpenAPI) set by All Access (coordinates(data)), TuEntrada (coordinates(page); Obelisco map placeholder already gives None) and Enigma (map pin, cached per venue in scrape). upsert_events -> _store_ticketer_points: first event by id per venue wins; skips VENUE_TO_BE_CONFIRMED (Enigma's "Argentina" pin is a city centre); never overwrites coords_source='manual'. test_openapi_contract now counts only published fields.
- L6 (2026-11-18) User: "si" -> T2 committed as 71333a1.
- L7 T3: Nominatim probed live 2026-11-18 (fixtures tests/fixtures/nominatim_*.json, limit=5). "Club Ciudad, Buenos Aires" returns 4 Buenos Aires province clubs before the CABA one; "Hipódromo de Palermo" returns 2 bus stops first. Rules: first result whose ISO3166-2-lvl4 equals the venue's region and whose category is not highway/place/boundary. Query "<name>, <city>, Argentina" (city = mode over its events); venues without a region are skipped. app/geocode.py + repository venues_to_geocode/store_geocoded; README section "Venue locations".
- L8 (2026-11-18) User: "SI" -> T3 committed as 727f033.
- L9 T4: GET /shows/{id} now answers ShowDetail = Show + venue_location {address|null, latitude, longitude} or null; GET /shows items unchanged (no join). Repository get_venue_location; show_detail_source reads it; schema exported, client schema.ts regenerated. Independent verifier launched over the whole feature (baseline f1344b9).
- L10 Verifier: S1-S3, S5, S6 met; S4 partial (Pulso read map coords only for the province); no change-caused blockers. Advisories: ticketer coords kept a stale OSM address; geocode.main is one transaction (a crash loses the run's lookups); ticketer coords not range-checked; case/space name variants are separate venues (pre-existing).
- L11 Correction batch: Pulso parse_event sets venue_point=coordinates(page); _store_ticketer_points sets address=None. RED both -> GREEN; full suite 800 passed (RUN_DB_TESTS=1). Remaining advisories left open for the user.
