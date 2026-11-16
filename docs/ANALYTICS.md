# Analytics (PostHog)

What recitAR reports, and how to read it. Everything is anonymous: no cookies, no accounts, no person profiles, nothing
about the visitor. The server sends the events (the app never loads a PostHog library), so ad blockers do not hide them.

## Events

| Event | When | Properties |
|---|---|---|
| `visit started` | The app opens (once per visit) | `device`, `environment` |
| `show opened` | A show page is opened | `show_key`, `show_name`, `venue`, `device`, `environment` |
| `filter used` | A filter is chosen on the home | `filter`, `value`, `device`, `environment` |
| `show shared` | The share button of a show is pressed | `show_key`, `show_name`, `venue`, `device`, `environment` |
| `more at venue clicked` | A card under "Más en <sala>" is opened; the show is the one clicked | `show_key`, `show_name`, `venue`, `device`, `environment` |
| `no results` | The listing is empty while a filter is on (once per combination) | `filters` (list), `venue`, `when` (range or day), `device`, `environment` |
| `ticket link clicked` | "Entradas" is clicked (counted by the `/go` redirect, crawlers excluded) | `show_key`, `show_name`, `venue`, `event_id`, `vendor`, `source`, `device`, `environment` |

`filter` is `search`, `venue`, `when`, `day` or `group`. `value` is the venue name, the quick range (`today`, `weekend`,
`week`, `month`), the picked day (`YYYY-MM-DD`) or the grouping (`month`, `week`, `day`). The search reports only that it
was used: what was typed is never sent. Clearing a filter reports nothing.

`source` of a ticket click is where in the app it came from (`show`, `spotlight`, `other`).

`device` is a coarse class the server works out from the request (`ios`, `android`, `desktop` or `unknown`): the web in
a phone browser and the native app both count as their phone. The browser's own text is never stored or sent, only this
label. It cannot tell the native app apart from a phone browser.

## Visits

A visit is a random id the app makes when it opens and keeps only in memory. Closing the tab or the app ends it, and a
reload starts another one. It is the PostHog `distinct_id` of that visit's `visit started`, `show opened` and
`filter used` events, so "unique users" in PostHog means visits, not people. `ticket link clicked` goes through the
redirect, which has no session, so each click has its own random id: count clicks by event count, not by users.

## Environments

Every event carries `environment` (`dev`, `test`, `prod`), taken from `APP_ENV` on the server (`dev` when unset; any other
value is reported as `unknown`). The Free plan has one project, so the three stages share it and are told apart by that
property. Set `APP_ENV` to `test` on the test deployment and `prod` on the main one.

## Server settings (`server/.env`)

- `POSTHOG_API_KEY`: the project's public key (`phc_...`). Without it nothing is sent.
- `POSTHOG_HOST`: `https://us.i.posthog.com` (default) or `https://eu.i.posthog.com`.
- `APP_ENV`: `dev`, `test` or `prod`.

In PostHog, switch on **Discard client IP data** (Settings → Project → IP data capture configuration): PostHog records
the IP of the request that reaches it, which is the server's.

## Building the dashboard (in PostHog, Product analytics)

One dashboard per environment: build the tiles once, then duplicate the dashboard and change its filter.

1. **Visits**: Trends, event `visit started`, "Unique users", chart by day.
2. **Shows opened**: Trends, event `show opened`, total count, breakdown by `show_name`.
3. **Most used filters**: Trends, event `filter used`, total count, breakdown by `filter`; a second one broken down by `value`.
4. **Ticket clicks**: Trends, event `ticket link clicked`, total count, breakdown by `show_name`; another by `venue` (which
   venue gets the most clicks) and another by `vendor`.
5. **Visits by device**: the visits insight with breakdown `device`.
   - **What people look for and do not find**: Table, event `no results`, breakdown `venue`, then another by `when`.
   - **Most shared shows**: Table, event `show shared`, breakdown `show_name`.
   - **Discovery from a venue**: Table, event `more at venue clicked`, breakdown `show_name`.
6. **Funnel** (optional): `visit started` → `show opened` → `ticket link clicked`, unique users. The last step has no
   session, so use the funnel for the first two steps only.
7. On the dashboard, add the filter `environment` = `prod` (then duplicate it for `test` and `dev`).
