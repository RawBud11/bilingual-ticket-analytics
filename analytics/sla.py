"""First-response SLA math: business minutes, due times, met or missed.

Ported from bilingual-sla-tracker/src/sla.js (JavaScript) to Python.
Times are naive datetimes in the team's time zone, read exactly as the export
writes them. No time zone conversion happens anywhere, so the same file gives
the same numbers on any computer.
"""

import re
from datetime import datetime, timedelta

import config

LOCAL_TIME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2}))?")


def parse_time(text):
    """"2026-10-23 10:00" (or ISO "2026-10-23T10:00:00") -> datetime, else None.

    Strict on purpose: "23/10/2026" could be day-first or month-first, so it is
    reported as unreadable instead of guessed. Seconds and any time zone suffix
    are ignored.
    """
    match = LOCAL_TIME_RE.match(str(text or "").strip())
    if not match:
        return None
    y, mo, d, h, mi = (int(g) if g else 0 for g in match.groups())
    try:
        return datetime(y, mo, d, h, mi)
    except ValueError:  # 2026-02-31, 25:00 ...
        return None


def is_business_day(day):
    return day.weekday() in config.BUSINESS_DAYS


def business_minutes_between(start, end):
    """Minutes between two times that fall inside business hours."""
    if end <= start:
        return 0
    total = 0
    day = datetime(start.year, start.month, start.day)
    while day < end:
        if is_business_day(day):
            open_ = max(day + timedelta(minutes=config.BUSINESS_START_MINUTE), start)
            close = min(day + timedelta(minutes=config.BUSINESS_END_MINUTE), end)
            if close > open_:
                total += (close - open_).total_seconds() / 60
        day += timedelta(days=1)
    return int(total)


def add_business_minutes(start, minutes):
    """The time when `minutes` business minutes have passed after `start`.
    A ticket created Friday 17:30 with 4 business hours is due Monday 11:30."""
    cursor, left = start, minutes
    for _ in range(400):  # safety stop: far more than any SLA in config.py
        day = datetime(cursor.year, cursor.month, cursor.day)
        open_ = day + timedelta(minutes=config.BUSINESS_START_MINUTE)
        close = day + timedelta(minutes=config.BUSINESS_END_MINUTE)
        if is_business_day(day) and cursor < close:
            begin = max(cursor, open_)
            if begin + timedelta(minutes=left) <= close:
                return begin + timedelta(minutes=left)
            left -= (close - begin).total_seconds() / 60
        cursor = day + timedelta(days=1)
    raise ValueError("add_business_minutes: SLA target too long")


def target(priority):
    return config.SLA_TARGETS.get(priority, config.SLA_TARGETS[config.FALLBACK_PRIORITY])


def sla_minutes_between(priority, start, end):
    """Minutes that count toward the SLA, on this priority's clock."""
    if target(priority)["clock"] == "24/7":
        return max(0, int((end - start).total_seconds() // 60))
    return business_minutes_between(start, end)


def sla_due(created, priority):
    goal = target(priority)
    if goal["clock"] == "24/7":
        return created + timedelta(minutes=goal["minutes"])
    return add_business_minutes(created, goal["minutes"])


def first_response_outcome(priority, created, first_response, as_of):
    """"met" or "missed" once the outcome is known at `as_of`, else None.

    Answered tickets: met when the reply came within the target.
    Unanswered tickets: "missed" once the target has passed (they already broke
    the SLA), None while there is still time (not counted either way).
    """
    goal = target(priority)["minutes"]
    if first_response is not None and first_response <= as_of:
        return "met" if sla_minutes_between(priority, created, first_response) <= goal else "missed"
    if sla_minutes_between(priority, created, as_of) >= goal:
        return "missed"
    return None
