# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

One shared recitAR design language across iOS, Android and web (single Expo / React Native codebase). Do not adapt the look per OS; respect only the native behaviors users expect (gestures, share sheet, safe areas, back navigation).

## Users

Concert-goers in Buenos Aires. Situation: deciding what to see, usually by date ("what's on Friday?") or by venue. Job: find a show, then reach the official ticket page in as few taps as possible.

## Product Purpose

recitAR aggregates Buenos Aires concerts (theatre and other categories later) and sends users to the **official** ticket page. It does not sell tickets. Success is measured as a funnel: session, filter use, event detail view, official ticket click. North star: ticket clicks.

## Positioning

All of Buenos Aires in one place: every show, across venues and ticketers, in a single calendar, always linking to the official source. Ticketer and venue sites only show their own catalogue; recitAR shows everything. Screens prioritize exploring and filtering the whole city.

## Operating Context

- Data comes from scraping official venue/ticketer sites (Teatro Colón, Niceto Club, Movistar Arena, Venti, more later), normalized into events, stored in our database, served by our API. The client never reads scraped sites directly.
- Ticket clicks go through our own redirect (`/go/<show-id>`) that logs the click and adds `utm_source`.
- Analytics: PostHog (`filter applied`, `event viewed`, `ticket link clicked`).

## Capabilities and Constraints

- v1: home with a carousel of relevant events and filters; filters by date, venue, and genre if the data allows; minimal show detail (artist, date, venue, large button to the official ticket link, source, "updated X ago"); one indexable URL per show.
- Carousel: small manual curation of featured events; fallback is the soonest events by date.
- Out of v1: accounts, favorites, alerts, ticket sales, non-concert categories (the data model already carries `category`).
- Scraped data is incomplete: UI must look right with missing image, price or time, inconsistent venue names, and multiple ticket vendors per show.
- SEO is a requirement: web output is `static` (static vs server still to be validated with many dynamic routes).
- UI copy: Spanish (Rioplatense, voseo) by default, with an English option for tourists. Every user-facing string exists in both languages.
- Undecided: final product name (recitAR is the working name; domain/INPI unchecked).

## Brand Commitments

- Working name: recitAR.
- Tone: clean, informative, youthful; easy to consult.
- Spanish voice uses voseo ("Elegí una fecha", "Comprá en la web oficial").

## Evidence on Hand

- Real scraped events from the venues above in the dev database, with artist photos from Wikimedia where licensed.
- No testimonials, users, partnerships, ticketer agreements, or traffic numbers exist. Do not fabricate them.
- Image policy: only images we are allowed to use; no copyrighted text or images copied from source sites.

## Product Principles

1. The whole city, one calendar: completeness of the listing is the core value.
2. Always official: every ticket path ends at the official source, never a reseller.
3. Honest about data: show source and freshness; degrade gracefully when fields are missing instead of hiding the show.
4. Few taps to the ticket: exploration must never get in the way of the ticket click.
5. Bilingual by default: no Spanish-only or English-only strings.
