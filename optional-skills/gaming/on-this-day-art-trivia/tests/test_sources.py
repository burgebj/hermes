"""Source-adapter parsing tests using cached fixtures."""

from __future__ import annotations


def test_britannica_parses_event_lines(britannica_fixture):
    from scripts import sources

    events = sources.parse_britannica_html(britannica_fixture)
    assert events, "expected at least one parsed event"
    by_year = {e.year: e for e in events if e.year is not None}
    assert 1967 in by_year
    ali = by_year[1967]
    assert "Muhammad Ali" in ali.summary
    assert ali.location is not None and "Houston" in ali.location
    assert ali.source == "britannica"


def test_britannica_extracts_country_when_present(britannica_fixture):
    from scripts import sources

    events = sources.parse_britannica_html(britannica_fixture)
    by_year = {e.year: e for e in events if e.year is not None}
    tito = by_year.get(2001)
    assert tito is not None
    assert tito.location and "Baikonur" in tito.location


def test_wikimedia_parses_events_births_deaths(wikimedia_fixture):
    from scripts import sources

    events = sources.parse_wikimedia_payload(wikimedia_fixture)
    cats = {e.category for e in events}
    assert "event" in cats
    assert "birth" in cats
    assert "death" in cats


def test_wikimedia_canonical_answer_uses_page_title(wikimedia_fixture):
    from scripts import sources

    events = sources.parse_wikimedia_payload(wikimedia_fixture)
    bounty = next(e for e in events if e.year == 1789)
    assert bounty.canonical_answer == "Mutiny on the Bounty"


def test_onthisday_parser_handles_year_prefixed_li():
    from scripts import sources

    html = "<html><body><ul>" \
           "<li>1903 First Tour de France was announced in Paris.</li>" \
           "<li>random unrelated copy without a year</li>" \
           "</ul></body></html>"
    events = sources.parse_onthisday_html(html)
    assert len(events) == 1
    assert events[0].year == 1903
    assert "Paris" in (events[0].location or "")
