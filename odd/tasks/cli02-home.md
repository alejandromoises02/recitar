# cli02: home in React Native

Objective: build the approved home ("The Night Marquee") in the Expo client, one section at a time, each testable on the user's iPhone (Expo Go) and the Android emulator before the next starts.
Branch: `dev` (one work-unit commit per section, with the user's OK). Delivery: ask-on-risk. Tests: vitest (`npx vitest run` in client/), typecheck `npx tsc --noEmit`, lint `npm run lint`.

## Specs

- S1. Ticket cli02, verbatim: "Construir la home según .impeccable/surfaces/home.md (sección \"Chosen design\") y DESIGN.md, con la maqueta .impeccable/mocks/home/home.html como referencia: marquesina de recién anunciados + abanico de destacados con recuadro; franja Próximos (8); agenda por mes con filtros fecha/lugar; en celular primero el abanico. Un show por fila con +N fechas; skeletons, error con reintento, sin resultados, imagen faltante; bilingüe (voseo + inglés). Depende de des03, api10, api11, api12 y api13. Skills: vercel-react-native-skills, make-interfaces-feel-better, transitions-dev/polish (Reanimated)."
- S2. Split by section so each stage can be tried on devices (user, L2).
- S3. Data comes from the API built in api10-13: `GET /shows` (one item per show, all dates, `name`, `first_seen_at`), `sort=announced&announced_from=<14 days ago>` for Just announced, `GET /featured` (`kind: picked | just_announced`), filters `q`, `from`, `to`, `venue`, `category`. The UI shows `name`, never the raw `title`.
- S4. Visual source of truth: DESIGN.md + `client/src/design/tokens.ts`; motion with Reanimated 4 and the motion tokens; no CSS variables, no hover-only behaviour on touch; respect reduced motion.
- S5. Fonts (Alfa Slab One, Unbounded, Onest, Barlow Condensed) installed as exact-pinned packages at least two weeks old, through the public npm registry (local .npmrc), never the corporate one.
- S6. The user runs Expo, emulators and devices personally; the assistant only gives the steps (memory feedback-user-runs-dev-tooling).
- S7. Spotify sample: official compact embed, visible, with Spotify branding (no hidden player); only for shows with a Spotify match; check play/pause on iOS and Android WebViews before building it.

## Tasks

| ID | Section | Specs | Route | Status | Commit |
|---|---|---|---|---|---|
| T1 | Base: fonts, theme, home screen frame (header logo, headline, responsive columns), Show domain + `useShows` / `useFeatured` queries | S1 S3 S4 S5 | inline | built, checks green; waiting for the user's device check | |
| T2 | Próximos strip: 8 soonest shows, "en N días", image fallback | S1 S3 | inline | todo | |
| T3 | Just announced: split-flap marquee board | S1 S3 S4 | inline | todo | |
| T4 | Featured: record-sleeve fan + spotlight card (CTA, ticket domain, trust line), autoplay with pause | S1 S3 S4 | inline | todo | |
| T5 | Spotify sample in the record (needs a Spotify match per show: api14) | S7 | inline | blocked by api14 | |
| T6 | Toda la cartelera: search, venue, type, when chips, 14-day strip, group by, grid, empty state | S1 S3 | inline | todo | |
| T7 | States and finish: skeletons, error + retry, English strings, accessibility pass | S1 S4 | inline | todo | |

## Log

- L1 (2026-11-13, user): "que es cli02?" then "dividiamos por secciones de la app para ir probando cada etapa entonces"
- L2: split agreed as T1-T7 above; T5 waits for api14 (Spotify artist per show) and the type chips in T6 wait for api15 (show type), both already on the board. Next: T1.
- L3 (2026-11-13): T1 built. Fonts @expo-google-fonts/* pinned (alfa-slab-one 0.4.1, unbounded 0.4.1, onest 0.4.2, barlow-condensed 0.4.1), public registry; loaded with useFonts behind the splash screen because Expo Go cannot embed fonts (vercel rule fonts-config-plugin applies once there is a dev build). Tokens fontFamily now name each loaded weight; typography has no fontWeight. Added Show/Featured domain + mappers, listShows/getFeatured, useShows/useFeatured, announcedFrom (BA day - 14), homeLayout (stacked <= 900 px, split 40/60), fluid sizes, BrandLogo with stepped shadow, SectionSlot placeholders that already show live counts. Checks: vitest 62 passed, tsc ok, lint ok, `expo export --platform android` bundles. Correction told to the user: the API does NOT run migrations on start; run `alembic upgrade head` in server/ first.
