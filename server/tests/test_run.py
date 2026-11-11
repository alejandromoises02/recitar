from datetime import datetime, timezone

import pytest

from app.domain.event import Event, TicketLink
from app.run import main, run

NOW = datetime(2026, 11, 8, tzinfo=timezone.utc)


def event(id_: str, title: str = "Show") -> Event:
    return Event(
        id=id_, category="concert", title=title, venue="V", starts_at=NOW,
        ticket_links=[TicketLink(vendor="X", url="https://x.com")], source_url="https://x.com/e", updated_at=NOW,
    )


class Recorder:
    """Stands in for the image step and for the database."""

    def __init__(self):
        self.enriched: list[Event] | None = None
        self.saved: list[Event] | None = None

    def enrich(self, events):
        self.enriched = list(events)
        return [e.model_copy(update={"title": e.title + "!"}) for e in events]

    def save(self, events):
        self.saved = list(events)


def broken():
    raise RuntimeError("site is down")


def test_events_of_every_source_are_enriched_then_saved():
    rec = Recorder()
    report = run({"a": lambda: [event("a-1")], "b": lambda: [event("b-1"), event("b-2")]}, rec.enrich, rec.save)
    assert [e.id for e in rec.enriched] == ["a-1", "b-1", "b-2"]
    assert [e.title for e in rec.saved] == ["Show!", "Show!", "Show!"]  # what was saved is what enrich returned
    assert report.counts == {"a": 1, "b": 2}
    assert report.saved == 3 and report.errors == {}


def test_a_source_that_fails_does_not_stop_the_others():
    rec = Recorder()
    report = run({"a": broken, "b": lambda: [event("b-1")]}, rec.enrich, rec.save)
    assert [e.id for e in rec.saved] == ["b-1"]
    assert report.errors == {"a": "RuntimeError: site is down"}
    assert report.counts == {"b": 1}


def test_only_the_chosen_sources_run():
    rec = Recorder()
    report = run({"a": broken, "b": lambda: [event("b-1")]}, rec.enrich, rec.save, only=["b"])
    assert report.errors == {} and report.counts == {"b": 1}


def test_an_unknown_source_is_an_error_that_lists_the_valid_ones():
    with pytest.raises(ValueError, match="nope.*a, b"):
        run({"a": lambda: [], "b": lambda: []}, Recorder().enrich, Recorder().save, only=["nope"])


def test_the_same_event_from_two_sources_is_saved_once():
    rec = Recorder()
    run({"a": lambda: [event("x-1", "old")], "b": lambda: [event("x-1", "new")]}, rec.enrich, rec.save)
    assert [(e.id, e.title) for e in rec.saved] == [("x-1", "new!")]


def many(prefix: str, count: int) -> list[Event]:
    return [event(f"{prefix}-{n}") for n in range(count)]


def test_a_source_that_returns_much_less_than_before_gets_a_warning_but_is_still_saved():
    rec = Recorder()
    report = run({"a": lambda: many("a", 4)}, rec.enrich, rec.save, known={"a": 10})
    assert "a" in report.warnings and "4" in report.warnings["a"] and "10" in report.warnings["a"]
    assert report.saved == 4  # upserts never delete, so a partial scrape cannot destroy anything


def test_a_normal_variation_is_not_a_warning():
    rec = Recorder()
    report = run({"a": lambda: many("a", 8)}, rec.enrich, rec.save, known={"a": 10})
    assert report.warnings == {}


def test_a_source_with_nothing_stored_yet_has_nothing_to_compare_with():
    rec = Recorder()
    report = run({"a": lambda: many("a", 1), "b": lambda: many("b", 1)}, rec.enrich, rec.save, known={"b": 0})
    assert report.warnings == {}


def test_when_nothing_was_scraped_nothing_is_saved():
    rec = Recorder()
    report = run({"a": lambda: [], "b": broken}, rec.enrich, rec.save)
    assert rec.enriched is None and rec.saved is None
    assert report.saved == 0 and "b" in report.errors


def test_an_unknown_source_on_the_command_line_fails_before_touching_the_database(monkeypatch, capsys):
    def no_database():
        raise AssertionError("the database must not be opened")

    monkeypatch.setattr("app.run.make_engine", no_database)
    assert main(["--only", "nope"]) == 2
    assert "nope" in capsys.readouterr().err



def test_venue_names_are_normalized_before_saving():
    recorder = Recorder()
    niceto_bar = event("venti-a").model_copy(update={"venue": "Niceto Bar"})
    run({"venti": lambda: [niceto_bar, event("venti-b")]}, recorder.enrich, recorder.save)
    assert [e.venue for e in recorder.saved] == ["Niceto Club", "V"]
