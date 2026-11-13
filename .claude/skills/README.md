# Project skills

Third-party skills vendored for this repo. Each folder keeps its original license file.

## Backend (`server/`)

All MIT-licensed.

| Skill | Source | Commit | Invocation |
|---|---|---|---|
| `fastapi-expert` | [Jeffallan/claude-skills](https://github.com/Jeffallan/claude-skills) `skills/fastapi-expert` | `078a25c` | automatic |
| `api-designer` | [Jeffallan/claude-skills](https://github.com/Jeffallan/claude-skills) `skills/api-designer` | `078a25c` | automatic |
| `testing-python-libraries` | [wdm0006/python-skills](https://github.com/wdm0006/python-skills) `skills/python/testing-strategy` | `36413e5` | automatic |
| `rendering-untrusted-content` | [wdm0006/python-skills](https://github.com/wdm0006/python-skills) `skills/common/rendering-untrusted-content` | `36413e5` | automatic |
| `verifying-external-behavior` | [wdm0006/python-skills](https://github.com/wdm0006/python-skills) `skills/common/verifying-external-behavior` | `36413e5` | automatic |
| `try-except` | [honnibal/claude-skills](https://github.com/honnibal/claude-skills) `try-except.md.txt` | `882fe89` | manual: `/try-except` |
| `tighten-types` | [honnibal/claude-skills](https://github.com/honnibal/claude-skills) `tighten-types.md.txt` | `882fe89` | manual: `/tighten-types` |
| `hypothesis-tests` | [honnibal/claude-skills](https://github.com/honnibal/claude-skills) `hypothesis-tests.md.txt` | `882fe89` | manual: `/hypothesis-tests` |

## Project decisions that win over the skills

- No user accounts: the API is public and read-only for everyone, so JWT/OAuth guidance does not apply. The only writes (PUT /featured) are for the one admin and use a static bearer token from `ADMIN_TOKEN` (see `server/app/api/admin_auth.py`), decided 2026-11-12.
- Database access is synchronous SQLAlchemy 2.0 + psycopg 3. Moving to async is a separate decision, not a default.
- Pagination is cursor-based (see `api-designer` `references/pagination.md`).

## Frontend (`client/`)

| Skill | Source | Commit | Invocation |
|---|---|---|---|
| `transitions-dev` | [Jakubantalik/transitions.dev](https://github.com/Jakubantalik/transitions.dev) `skills/transitions-dev` | `20d70c1` | automatic, or `transitions reveal/review/apply/refine` |
| `transitions-polish` | [Jakubantalik/transitions.dev](https://github.com/Jakubantalik/transitions.dev) `skills/transitions-polish` | `20d70c1` | automatic, or `transitions review/polish` |
| `vercel-react-native-skills` | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) `skills/react-native-skills` | `1a2c79d` | automatic |
| `make-interfaces-feel-better` | [jakubkrehel/make-interfaces-feel-better](https://github.com/jakubkrehel/make-interfaces-feel-better) `skills/make-interfaces-feel-better` | `35545ea` | automatic (quick or full review) |

Licenses: `make-interfaces-feel-better` is MIT (`LICENSE`). `vercel-react-native-skills` is MIT as declared in its `SKILL.md` (the upstream repo ships no license file). The transitions skills use the Transitions.dev license (`LICENSE.txt` in each folder): free for personal and commercial use, no redistribution of the library itself. Installed with `npx skills@1.7.4 add`; `skills-lock.json` records the content hashes.

Also used, not vendored: the Impeccable plugin (`pbakaus/impeccable`, Apache-2.0), enabled at project scope in `.claude/settings.json`.

### Project decisions that win over the frontend skills

- The client is Expo / React Native (iOS, Android, web). The transitions.dev recipes are web CSS: translate each one to Reanimated 4 (CSS-style `transition*` style props, keyframe animations, or `useAnimatedStyle`). Never ship CSS custom properties, `:hover` selectors, or `@keyframes` blocks, and never copy `_root.css` into the client.
- Motion tokens (durations, easings, distances, scales) live in one shared TypeScript module in the client, with values taken from the skills' `_root.css` scale. Components import tokens; no hardcoded durations or easing curves.
- Hover rules apply only on web; on touch devices use the pressed state instead.
- Respect reduced motion (Reanimated `useReducedMotion` / `ReduceMotion`).
- `vercel-react-native-skills` is the native-first source: for how a component is built (lists, Reanimated, navigation, fonts) it wins over web-oriented examples in the other skills. Library swaps it suggests (for example Legend List or FlashList instead of `FlatList`) are separate decisions: ask first, pin an exact version at least two weeks old.
- `make-interfaces-feel-better` examples are web CSS; apply the principle, not the snippet. React Native equivalents: tabular numbers -> `fontVariant: ['tabular-nums']`; minimum hit area -> `hitSlop` or padding on `Pressable`; scale on press -> `Pressable` pressed state animated with Reanimated; shadows -> `boxShadow` style prop. Web-only rules (font smoothing, `text-wrap`, `will-change`, `transition: all`) apply only to web-specific code.
- GSAP was evaluated and rejected (2026-11-11): it animates the DOM and `window` scroll, which do not exist on iOS/Android. Scroll-driven and list animations use Reanimated (`entering` animations, `useAnimatedScrollHandler`). Reconsider GSAP only for a separate web landing page.

To update a skill, re-copy it from its source at a newer commit and update this table.
