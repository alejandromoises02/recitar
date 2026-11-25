# Free demo deploy

A public link to show the app while production (Azure, board card dep01) waits for the final name and
domain. Both hosts below are free and need no card, so the demo can never be billed: at worst a
host suspends it.

| Part | Host | Notes |
|---|---|---|
| Web (Expo static export) | Cloudflare Pages | Rebuilt on every push to `dev`. |
| API (FastAPI) | Render, free plan | Sleeps after 15 minutes idle; the first request then takes about a minute. Open the link a minute before showing it. |
| Database | Neon branch `dev` | The same data as local development. |
| Scraper | Your Mac | Run `python -m app.run` to refresh the shows the demo lists. |

The demo is public: anyone with the link sees it. It is not the launch.

## 1. API on Render

1. Sign in at render.com with GitHub and allow access to the `recitar` repository.
2. New > Blueprint, pick the repository. Render reads `render.yaml` at the repository root and
   proposes the service `recitar-api-demo` (branch `dev`, folder `server`).
3. It asks for the secrets marked `sync: false`. Copy them from `server/.env`:
   - `DATABASE_URL` and `DATABASE_URL_POOLED`: the Neon `dev` branch URLs.
   - `CORS_ORIGINS`: leave it empty for now; step 3 fills it.
   - `SCRAPER_CONTACT_EMAIL`: the recitAR contact address from `server/.env`. Wikimedia asks for a
     contact, and the build needs it to rebuild the licensed artist photos (Movistar Arena shows).
4. Create it. The build installs the dependencies and runs `python -m app.images.restore`, which
   downloads the image copies again (the host's disk starts empty and `server/data/` is not in git).
   The build log ends with `image copies: N present, M failed` and `licensed photos: N present, M
   failed` (or `skipped` when `SCRAPER_CONTACT_EMAIL` is missing).
5. Open `https://<service>.onrender.com/health`: it answers `{"status": "ok"}`.

## 2. Web on Cloudflare Pages

1. Sign in at dash.cloudflare.com, then Workers & Pages > Create > Pages > Connect to Git, pick the
   repository and the `dev` branch.
2. Build settings:
   - Root directory: `client`
   - Build command: `npm run build:web` (the Expo export, then `scripts/flatten-web-assets.mjs`: Pages
     never uploads folders named `node_modules`, where Expo puts the font files)
   - Build output directory: `dist`
3. Environment variables:
   - `EXPO_PUBLIC_API_URL` = `https://<service>.onrender.com` (from step 1)
   - `NODE_VERSION` = `22.23.4`
4. Deploy. The site is at `https://<project>.pages.dev`. `client/public/_redirects` sends every
   `/show/<id>` address to the one page Expo exports for shows.

## 3. Let the web call the API

In Render, set `CORS_ORIGINS` to the Pages address (`https://<project>.pages.dev`, no trailing
slash) and save; Render restarts the service. Without it the browser blocks every call and the
home stays empty.

## Known limits

- Requests reach the API through Render's proxy, so the per-IP limit (api20) sees one address for
  everyone. Fine for a demo; production sets `--forwarded-allow-ips` (dep01 point 10).
- No analytics: `POSTHOG_API_KEY` is not set, so nothing is sent.
- No admin endpoints: `ADMIN_TOKEN` is not set, so they reject every call.
