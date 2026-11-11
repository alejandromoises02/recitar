"""Writes the API's OpenAPI schema to the client, which generates its TypeScript types from it.

Run `python -m app.openapi_export` here after changing the API, then `npm run gen:api` in client/.
A test fails while the client's copy is out of date.
"""

import json

from app.db import SERVER_DIR
from app.main import app

CLIENT_SCHEMA = SERVER_DIR.parent / "client" / "src" / "api" / "openapi.json"


def schema_json() -> str:
    return json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    CLIENT_SCHEMA.parent.mkdir(parents=True, exist_ok=True)
    CLIENT_SCHEMA.write_text(schema_json())
    print(f"wrote {CLIENT_SCHEMA.relative_to(SERVER_DIR.parent)}")


if __name__ == "__main__":
    main()
