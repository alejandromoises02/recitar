# Brief: recitAR (working name)

Status: draft v1, 2026-10-25. Source of truth for decisions: Engram project `recis`, topic `concerts-app/brief`.

## Product

A Buenos Aires event aggregator. It lists concerts (theatre and other shows later) and sends users to the **official** ticket page. It does not sell tickets.

## Audience and main job

- Audience: concert-goers in Buenos Aires.
- Main job: find a show by date or venue, then jump to the official ticket link in as few taps as possible.

## Platforms and SEO

- iPhone, Android and web from day one, one Expo / React Native codebase.
- Best possible SEO is a requirement. Web output must be `static` or `server` from the start (the default `single` has no indexable HTML). Static vs server is undecided and must be tested with many dynamic event routes.
- Keep data and logic separate from UI so the web can later move to a stronger SEO stack if needed.

## v1 scope

In:
- Home with a carousel of relevant events and filters.
- Filters: date, venue, and genre if the scraped data allows it.
- Minimal show detail page: artist, date, venue, large button to the official ticket link, source, "updated X ago". One indexable URL per show.

Out for v1: accounts, favorites, alerts, ticket sales, theatre and other categories (the data model still carries an event `category` field from day one).

Carousel rule: small manual curation of featured events; fallback is the soonest events by date.

## Tone

Clean, informative, youthful. Easy to consult. No visual references yet.

## Data

- Source: scraping small local sites first (suggested order: Teatro Colon, Niceto Club, Movistar Arena). APIs later if obtainable. Manual entry is not viable.
- Scrape defensively: respect robots.txt, throttle, store facts only (artist, date, venue), no copyrighted text or images, always link to the official source.
- Scraped data is incomplete. The UI must look right with missing image, price or time, inconsistent venue names, and multiple ticket vendors per show.

## Success metrics

Funnel: session, filter use, event detail view, official ticket click. North star: ticket clicks.

- Analytics: PostHog.
- Ticket clicks go through an own redirect (`/go/<show-id>`) that logs the click and adds `utm_source`, so the number is reliable when talking to ticketers.
- Suggested events: `filter applied` (type), `event viewed` (event_id, source), `ticket link clicked` (event_id, vendor).

## Open items

- Final name and its availability (domain, INPI).
- `static` vs `server` web rendering.
- Visual references and a design system (frontend-design, UI/UX Pro Max and Figma are set up for this).
