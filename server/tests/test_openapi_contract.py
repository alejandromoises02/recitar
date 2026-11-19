"""The client's TypeScript types are generated from the OpenAPI schema (see client/README.md), so the
schema must say exactly what the API sends, and the copy the client is built from must be current."""

import json

from app.domain.event import Event, Show, ShowDateTickets, ShowDetail, VenueLocation
from app.main import app
from app.openapi_export import CLIENT_SCHEMA, schema_json


def test_every_event_field_is_required_because_the_api_always_sends_it():
    # Fields with a default (artist, city, image_*...) are still sent, as null; without this they
    # would be optional in the generated types and the client would have to handle a missing field.
    schemas = app.openapi()["components"]["schemas"]
    published = {name for name, field in Event.model_fields.items() if not field.exclude}  # venue_point stays in
    sent = published | set(Event.model_computed_fields)  # computed `name` is sent too
    assert "venue_point" not in schemas["Event"]["properties"]
    assert set(schemas["Event"]["required"]) == sent
    assert set(schemas["EventDetail"]["required"]) == sent | {"other_dates"}
    assert set(schemas["Show"]["required"]) == set(Show.model_fields)
    assert set(schemas["ShowDateTickets"]["required"]) == set(ShowDateTickets.model_fields)
    assert set(schemas["ShowDetail"]["required"]) == set(ShowDetail.model_fields)
    assert set(schemas["VenueLocation"]["required"]) == set(VenueLocation.model_fields)  # address is sent as null


def test_the_exported_schema_is_the_one_the_api_serves():
    assert json.loads(schema_json()) == app.openapi()


def test_the_clients_copy_of_the_schema_is_current():
    assert CLIENT_SCHEMA.exists(), "run `python -m app.openapi_export` in server/"
    assert CLIENT_SCHEMA.read_text() == schema_json(), (
        "The API changed: run `python -m app.openapi_export` in server/, then `npm run gen:api` in client/."
    )
