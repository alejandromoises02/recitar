# Surface brief: Show detail

Status: confirmed 2026-11-15 (impeccable shape). Reference mock: `.impeccable/mocks/show/show.html` (local only, gitignored), with real shows for one, two and seven dates, desktop and phone.

## Job and audience
- A concert-goer who tapped a show anywhere on the home (board, Próximos, explore card, spotlight) or arrived from a shared link or a search engine. They want to confirm what, where and when, pick a date, and reach the official ticket page.
- Mode: Operate. Success: the ticket click (north star), through our `/go/<id>` redirect.

## Content
- Photo, whole (never cropped), on a blurred copy of itself; the poster takes the photo's shape between portrait 3:4 and landscape 4:3. Credit badge on the photo when licensed: "Foto: <author> · <license>" with links. Typographic fallback when there is no photo.
- A banner (a photo at least twice as wide as tall, like Teatro Gran Rivadavia's 900x300) would be a thin strip in the poster column: on desktop the page drops the poster column and the banner goes whole under the name and venue line, above the dates (decided 2026-11-24; every other photo keeps the poster column, reaching the bottom of the info).
- Show name (Unbounded display; shrinks to fit a long single word on phones, never breaks a word), then venue · "N fechas" (yellow) · type.
- Dates and tickets: see Selected direction.
- "Entradas en <ticket domain>" under the button.
- "Escuchalo": the official Spotify compact embed (api14), between the trust line and "Cómo llegar". The section is absent when the show has no Spotify match. Web plays full tracks; in the app's WebView Spotify plays short previews and shows its own "get Spotify" banner now and then (accepted 2026-11-24). The player is removed when the page leaves view or the app goes to the background, so the audio stops.
- Trust line: "recitAR no vende entradas: te lleva a la página oficial de cada show." plus "Datos de <source domain> · actualizado hace X".
- Share button (44 px circle beside the name): native share sheet on iOS / Android, copy link on web.
- "Más en <venue>": up to 4 other shows at the same venue as show cards (same card as explore), never the current show; a sideways scroll row on phones.

## Selected direction (decided 2026-11-15)
- **Option B: pick a date, one button.** Date tiles (weekday, day in Unbounded, month, time; the year when not this year), single choice, the next date selected on arrival; one primary button "Entradas" with the chosen date under it ("Mié 18/11 · 21:00"). Tiles are a radiogroup.
- **One date:** no tiles. The date in large yellow board type ("MAR 01/12 21:00") and the button.
- **Phones:** the ticket button is pinned at the bottom of the screen at all times and follows the chosen tile; the in-page button is not repeated. Desktop: the button sits under the tiles, in view with the name.
- Desktop: two columns, poster 5 / info 7; "Más en <venue>" full width below. Phones: one column (poster, name, meta, tiles, Spotify, trust, more) with the pinned bar.
- Same world as the home (DESIGN.md "The Night Marquee"): warm ink, cream text, yellow only for dates, selection and the way to tickets; a blurred tint of the photo behind the top of the page.

## States and ranges
- Dates: 1, 2 to a few, and many (7+ seen; tiles wrap). Past dates are not listed.
- Missing photo, missing time ("Hora a confirmar"), several ticket vendors on one date (one button per vendor under the tiles), show without Spotify match, unknown show id (404 page with a way back to the listing).
- Loading: skeleton in the page's shape. API error: message and retry.

## Constraints
- One URL per show (`/show/<id>`), indexable on web (title, description, share preview).
- Bilingual (es voseo / en); WCAG 2.2 AA, covered by `npm run test:a11y` once built.
- Every ticket link goes through `/go/<id>` (t11) and logs the click; analytics events `event viewed` and `ticket link clicked` (t12).

## Out of v1
Calendar add (fut01), favorites and lists (fut02), reminders (fut03).
