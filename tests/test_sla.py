# Ported from bilingual-sla-tracker/tests/sla.test.js (JavaScript -> Python).
# Business hours Mon-Fri 08:00-18:00, urgent on a 24/7 clock.
# 2026-10-23 is a Friday, 2026-10-24/25 the weekend, 2026-10-26 a Monday.
from datetime import datetime

import pytest

from analytics.sla import (business_minutes_between, first_response_outcome, parse_time,
                           sla_due)


def at(text):
    return parse_time(text)


def test_parse_time_accepts_local_and_iso():
    assert at("2026-10-23 10:00") == datetime(2026, 10, 23, 10, 0)
    assert at("2026-10-23T07:05:59") == datetime(2026, 10, 23, 7, 5)
    assert at("2026-10-23") == datetime(2026, 10, 23)


@pytest.mark.parametrize("text", ["", None, "23/10/2026 10:00", "2026-02-31 10:00",
                                  "2026-10-23 25:00", "yesterday"])
def test_bad_dates_give_none_not_a_guess(text):
    assert at(text) is None


@pytest.mark.parametrize("start,end,minutes", [
    ("2026-10-23 09:00", "2026-10-23 10:30", 90),   # inside one business day
    ("2026-10-23 06:00", "2026-10-23 08:00", 0),    # before hours
    ("2026-10-23 06:00", "2026-10-23 09:00", 60),
    ("2026-10-23 17:00", "2026-10-23 22:00", 60),   # after hours
    ("2026-10-23 17:00", "2026-10-26 09:00", 120),  # the weekend does not count
    ("2026-10-24 09:00", "2026-10-25 17:00", 0),
    ("2026-10-23 10:00", "2026-10-23 09:00", 0),    # end before start
])
def test_business_minutes(start, end, minutes):
    assert business_minutes_between(at(start), at(end)) == minutes


@pytest.mark.parametrize("created,priority,due", [
    ("2026-10-21 09:00", "high", "2026-10-21 13:00"),
    ("2026-10-16 17:30", "high", "2026-10-19 11:30"),   # Friday 17:30 -> Monday 11:30
    ("2026-10-22 06:15", "high", "2026-10-22 12:00"),   # clock starts at 08:00
    ("2026-10-22 19:40", "normal", "2026-10-23 16:00"),  # next business morning
    ("2026-10-24 11:00", "normal", "2026-10-26 16:00"),  # Saturday -> Monday
    ("2026-10-22 14:00", "low", "2026-10-26 10:00"),    # spans the weekend
    ("2026-10-24 02:00", "urgent", "2026-10-24 03:00"),  # 24/7
    ("2026-10-23 17:30", "urgent", "2026-10-23 18:30"),
    ("2026-10-21 08:00", "whatever", "2026-10-21 16:00"),  # unknown -> normal
])
def test_due_time(created, priority, due):
    assert sla_due(at(created), priority) == at(due)


def test_answered_in_time_is_met_late_is_missed():
    now = at("2026-10-23 10:00")
    assert first_response_outcome("high", at("2026-10-16 17:30"), at("2026-10-19 11:30"), now) == "met"
    assert first_response_outcome("high", at("2026-10-16 17:30"), at("2026-10-19 11:31"), now) == "missed"


def test_unanswered_counts_only_once_the_target_has_passed():
    created = at("2026-10-23 08:00")  # high: 240 business minutes
    assert first_response_outcome("high", created, None, at("2026-10-23 11:59")) is None
    assert first_response_outcome("high", created, None, at("2026-10-23 12:00")) == "missed"
    # Friday 16:00: the weekend adds nothing.
    assert first_response_outcome("high", at("2026-10-23 16:00"), None, at("2026-10-25 23:00")) is None


def test_urgent_counts_nights_and_weekends():
    created = at("2026-10-24 02:00")  # Saturday
    assert first_response_outcome("urgent", created, None, at("2026-10-24 02:59")) is None
    assert first_response_outcome("urgent", created, None, at("2026-10-24 03:00")) == "missed"
    assert first_response_outcome("urgent", created, at("2026-10-24 03:00"), at("2026-10-26 09:00")) == "met"


def test_a_reply_after_as_of_is_not_counted_yet():
    created = at("2026-10-21 09:00")
    outcome = first_response_outcome("high", created, at("2026-10-21 10:00"), at("2026-10-21 09:30"))
    assert outcome is None
