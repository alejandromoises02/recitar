# Project skills

Third-party skills vendored for backend work (`server/`). All are MIT-licensed; each folder keeps its original `LICENSE`.

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

- No authentication: the API is public and read-only, so JWT/OAuth guidance does not apply.
- Database access is synchronous SQLAlchemy 2.0 + psycopg 3. Moving to async is a separate decision, not a default.
- Pagination is cursor-based (see `api-designer` `references/pagination.md`).

To update a skill, re-copy it from its source at a newer commit and update this table.
