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

## Backend skills

All backend work (`server/`) follows the skills in `.claude/skills/` (see its `README.md` for sources and the project decisions that override them). Before writing or reviewing backend code, load the ones that apply: `fastapi-expert` and `api-designer` for the API, `testing-python-libraries` for tests, `verifying-external-behavior` for scrapers, `rendering-untrusted-content` for any scraped text that reaches a client. Run `/try-except` and `/tighten-types` on touched modules before closing a backend feature.

## Code conventions

- Comments: few, in English, only when the code cannot say it (a non-obvious why, a platform quirk). Never quote Spanish UI copy in a comment; UI copy lives in the `strings.ts` tables.
- Client components stay short and clean:
  - Styles go in a sibling `<Component>.styles.ts` (`StyleSheet.create` there), never inside the component file.
  - Constants go in a sibling `<Component>.constants.ts` when only that component uses them, or in a shared constants module (feature-level `*.constants.ts`, or `client/src/design/tokens.ts` for design values) when several do.
  - Reuse styles: shared style pieces live in a shared `*.styles.ts` and are spread into each component's styles instead of being copied.
  - One component per file; a component with sub-parts gets its own folder.

## Frontend skills

UI work in `client/` follows the Impeccable plugin (how it looks), `vercel-react-native-skills` (how it is built: lists, animation, performance), and the `make-interfaces-feel-better`, `transitions-dev` and `transitions-polish` skills. Their examples are web CSS; apply the principles with React Native equivalents. The transitions.dev recipes are web CSS and the client is React Native: translate them to Reanimated 4 and keep motion tokens in a shared TypeScript module, never CSS variables. See `.claude/skills/README.md` for the full rules.
