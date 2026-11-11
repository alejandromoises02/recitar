"""The client's TypeScript types are generated from the OpenAPI schema (see client/README.md), so the
schema must say exactly what the API sends, and the copy the client is built from must be current."""

import json

from app.domain.event import Event
from app.main import app
from app.openapi_export import CLIENT_SCHEMA, schema_json


def test_every_event_field_is_required_because_the_api_always_sends_it():
    # Fields with a default (artist, city, image_*...) are still sent, as null; without this they
    # would be optional in the generated types and the client would have to handle a missing field.
    schemas = app.openapi()["components"]["schemas"]
    assert set(schemas["Event"]["required"]) == set(Event.model_fields)
    assert set(schemas["EventDetail"]["required"]) == set(Event.model_fields) | {"other_dates"}


def test_the_exported_schema_is_the_one_the_api_serves():
    assert json.loads(schema_json()) == app.openapi()


def test_the_clients_copy_of_the_schema_is_current():
    assert CLIENT_SCHEMA.exists(), "run `python -m app.openapi_export` in server/"
    assert CLIENT_SCHEMA.read_text() == schema_json(), (
        "The API changed: run `python -m app.openapi_export` in server/, then `npm run gen:api` in client/."
    )
