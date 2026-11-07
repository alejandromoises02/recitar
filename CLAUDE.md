# recitAR

Buenos Aires event aggregator. Links to official ticket pages; does not sell tickets. See `docs/BRIEF.md`.

## Branching

- `dev`: integration branch, local work happens here. Feature branches (`feat/...`, `fix/...`) start from `dev`.
- `test`: test deployments. Promoted from `dev`.
- `main`: main deployment. Promoted from `test` only after testing.

Rules (GitHub branch protection is unavailable on the free private plan, so this is by discipline):

- Never push directly to `test` or `main`. Changes reach them only through a pull request.
- Promotion order is `dev` -> `test` -> `main`. Never skip a step.
- Do not commit, push, or open a PR without the user's explicit OK.

## Commits

- Conventional commits only (`feat:`, `fix:`, `chore:`, `docs:`, ...).
- NEVER add `Co-Authored-By`, "Generated with Claude Code", or any AI attribution anywhere (commits, PRs, issues, docs, code). No exceptions.
- Repo-local git identity is personal; do not change the global (work) identity.

## Layout

Monorepo (decided): one repo, one folder per deployable. A single Python backend, `server/` (API with FastAPI + scraper + AI features), will be added next to `client/` (TypeScript). It is not created yet. The client only talks to the API; its TypeScript types are generated from the API's OpenAPI schema.

Database (decided, not configured yet): Neon Postgres (free plan, pgvector available for semantic search). Server hosting is still undecided: Google Cloud Run (scales to zero, free quotas unverified) vs Render free (sleeps after 15 min, ~1 min cold start). Render's free Postgres was discarded (expires after 30 days).

Goal: the project doubles as an AI-engineering portfolio piece. Planned AI work, in order: LLM extraction of events from messy pages + an evals suite (golden cases, accuracy, cost/latency), semantic search/recommendations with embeddings, then a tool-using chat assistant grounded in our own events.

Data flow: scraper -> normalize to `Event` -> our database -> API -> client. The client never reads scraped sites directly.

- `client/`: Expo / React Native app (iOS, Android, web). Feature-first folders under `client/src/features/`.
- `docs/`: project docs.
